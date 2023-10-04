# -*- coding: utf-8 -*-

import tempfile
import binascii
import xlrd
from datetime import date, datetime
from odoo.exceptions import Warning, UserError
from odoo.osv import osv
from odoo import models, fields, exceptions, api, _
import logging
_logger = logging.getLogger(__name__)
import io
try:
	import csv
except ImportError:
	_logger.debug('Cannot `import csv`.')
try:
	import xlwt
except ImportError:
	_logger.debug('Cannot `import xlwt`.')
try:
	import cStringIO
except ImportError:
	_logger.debug('Cannot `import cStringIO`.')
try:
	import base64
except ImportError:
	_logger.debug('Cannot `import base64`.')

class AddDocInvoiceRelacWizard(models.TransientModel):
	_name = 'add.doc.invoice.relac.wizard'
	_description = 'Add Doc Invoice Relac Wizard'

	document_file = fields.Binary(string='Excel')
	name_file = fields.Char(string='Nombre de Archivo')

	def importar(self):
		if not self.document_file:
			raise UserError('Tiene que cargar un archivo.')
		
		try:
			fp = tempfile.NamedTemporaryFile(delete= False,suffix=".xlsx")
			fp.write(binascii.a2b_base64(self.document_file))
			fp.seek(0)
			workbook = xlrd.open_workbook(fp.name)
			sheet = workbook.sheet_by_index(0)
			move_ids = []
		except:
			raise Warning(_("Archivo invalido!"))

		for row_no in range(sheet.nrows):
			if row_no <= 0:
				continue
			else:
				line = list(map(lambda row:isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
				if len(line) == 9:
					date_string = None
					if line[3] != '':
						a1 = int(float(line[3]))
						a1_as_datetime = datetime(*xlrd.xldate_as_tuple(a1, workbook.datemode))
						date_string = a1_as_datetime.date().strftime('%Y-%m-%d')
					values = ({'journal_id':line[0],
								'asiento_nro':line[1],
								'type_document_id': line[2],
								'date': date_string,
								'nro_comprobante':line[4],
								'total_me':line[5],
								'total_mn': line[6],
								'base_imp': line[7],
								'igv': line[8],
								})
				elif len(line) > 9:
					raise Warning(_('Tu archivo tiene columnas mas columnas de lo esperado.'))
				else:
					raise Warning(_('Tu archivo tiene columnas menos columnas de lo esperado.'))
				
				res = self.add_doc_relac_move(values)
				move_ids.append(res)

		for res in move_ids: 
			if res.state in ['draft']:
				res.post()

		return self.env['popup.it'].get_message(u'SE AGREGARON CON EXITO LOS DOC RELACIONADOS EN LOS ASIENTOS.')

	def add_doc_relac_move(self, values):
		move_obj = self.env['account.move']

		if str(values.get('asiento_nro')) == '':
			raise Warning(_('El campo "asiento_nro" no puede estar vacio.'))
		if str(values.get('journal_id')) == '':
			raise Warning(_('El campo "journal_id" no puede estar vacio.'))
		if str(values.get('type_document_id')) == '':
			raise Warning(_('El campo "type_document_id" no puede estar vacio.'))

		s = str(values.get("journal_id"))
		code = s.rstrip('0').rstrip('.') if '.' in s else s
		journal_id = self.find_journal(code)

		s = str(values.get("type_document_id"))
		code = s.rstrip('0').rstrip('.') if '.' in s else s
		type_document_id = self.find_type_document(code)

		move_search = move_obj.search([
					('name', '=', values.get('asiento_nro')),
					('journal_id','=',journal_id.id),
					('company_id','=',self.env.company.id)
				],limit=1)

		if move_search:
			vals = {
				'type_document_id':type_document_id.id if type_document_id else None,
				'date': values.get("date"),
				'nro_comprobante': values.get("nro_comprobante"),
				'amount_currency': values.get("total_me") if values.get("total_me") else 0,
				'amount': values.get("total_mn") if values.get("total_mn") else 0,
				'bas_amount':values.get("base_imp") if values.get("base_imp") else 0,
				'tax_amount': values.get("igv") if values.get("igv") else 0
			}
			move_search.write({'doc_invoice_relac' :([(0,0,vals)]) })
			return move_search

		else:
			raise UserError(u'No se encontró el asiento con el numero "%s" y el diario "%s"' % (values.get('asiento_nro'),values.get("journal_id")))

	def find_journal(self,code):
		journal_search = self.env['account.journal'].search([('code','=',code),('company_id','=',self.env.company.id)],limit=1)
		if journal_search:
			return journal_search
		else:
			raise Warning(_('No existe el diario "%s" en la Compañia.') % code)

	def find_type_document(self,code):
		catalog_payment_search = self.env['l10n_latam.document.type'].search([('code', '=', str(code))],limit=1)
		if catalog_payment_search:
			return catalog_payment_search
		else:
			raise Warning(_('No existe un Tipo de Comprobante con el Codigo "%s"') % code)

	def download_template(self):
		return {
			 'type' : 'ir.actions.act_url',
			 'url': '/web/binary/download_template_add_doc_invoice_relac_example',
			 'target': 'new',
			 }