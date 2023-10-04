# -*- coding: utf-8 -*-

import time
from datetime import datetime
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

class ImportDetracWizard(models.TransientModel):
	_name = 'import.detrac.wizard'
	_description = 'Import Detrac Wizard'

	document_file = fields.Binary(string='Excel')
	name_file = fields.Char(string='Nombre de Archivo')
	journal_id = fields.Many2one('account.journal',string='Diario')

	def importar(self):
		if not self.document_file:
			raise UserError('Tiene que cargar un archivo.')
		
		if not self.journal_id:
			raise UserError('Tiene que escoger un Diario')
		
		try:
			fp = tempfile.NamedTemporaryFile(delete= False,suffix=".xlsx")
			fp.write(binascii.a2b_base64(self.document_file))
			fp.seek(0)
			workbook = xlrd.open_workbook(fp.name)
			sheet = workbook.sheet_by_index(0)
		except:
			raise Warning(_("Archivo invalido!"))

		for row_no in range(sheet.nrows):
			if row_no <= 0:
				continue
			else:
				line = list(map(lambda row:isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
				if len(line) == 7:
					date_string = None
					if line[3] != '':
						a1 = int(float(line[3]))
						a1_as_datetime = datetime(*xlrd.xldate_as_tuple(a1, workbook.datemode))
						date_string = a1_as_datetime.date().strftime('%Y-%m-%d')
					values = ({'serie':line[0],
								'ref':line[1],
								'ruc':line[2],
								'date': date_string,
								'nro_comprobante':line[4],
								'type_op_det' : line[5],
								'detraction_percent_id' : line[6],
								})
				elif len(line) > 7:
					raise Warning(_('Tu archivo tiene columnas mas columnas de lo esperado.'))
				else:
					raise Warning(_('Tu archivo tiene columnas menos columnas de lo esperado.'))
				
				self.add_doc_relac_move(values)

		return self.env['popup.it'].get_message(u'SE ACTUALIZARON EXITOSAMENTE LAS FACTURAS.')

	def add_doc_relac_move(self, values):
		move_obj = self.env['account.move']
		if str(values.get('serie')) == '':
			raise Warning(_('El campo "Serie de Comprobante" no puede estar vacio.'))
		if str(values.get('ref')) == '':
			raise Warning(_('El campo "Numero de Comprobante" no puede estar vacio.'))
		if str(values.get('ruc')) == '':
			raise Warning(_('El campo "RUC Proveedor" no puede estar vacio.'))
		if str(values.get('type_op_det')) == '':
			raise Warning(_('El campo "Tipo de Operación" no puede estar vacio.'))
		if str(values.get('detraction_percent_id')) == '':
			raise Warning(_('El campo "Bien o Servicio" no puede estar vacio.'))

		s = str(values.get("serie"))
		serie = s.rstrip('0').rstrip('.') if '.' in s else s

		s = str(values.get('ref'))
		ref_s = s.rstrip('0').rstrip('.') if '.' in s else s
		ref = self.get_text_with_size(ref_s,8,'0',False)

		s = str(values.get('ruc'))
		ruc = s.rstrip('0').rstrip('.') if '.' in s else s
		partner_id = self.find_partner(ruc)

		s = str(values.get('nro_comprobante'))
		nro_comprobante = s.rstrip('0').rstrip('.') if '.' in s else s

		doc = self.env['l10n_latam.document.type'].search([('code','=','01')],limit=1)

		type_op_det = str(values.get('type_op_det'))
		move_search = move_obj.search([
					('l10n_latam_document_type_id','=',doc.id),
					('ref','=',serie+'-'+ref),
					('journal_id','=',self.journal_id.id),
					('partner_id','=',partner_id.id),
					('company_id','=',self.env.company.id)
				],limit=1)
		detraction_percent_id = self.env['detractions.catalog.percent'].search([('code','=',str(values.get('detraction_percent_id')))],limit=1)
		if not detraction_percent_id:
			raise Warning(_('No existe un Bien o Servicio con el codigo "%s"') % str(values.get('detraction_percent_id')))
		#
		if move_search:

			move_search.write({
				'date_detraccion': values.get("date") if values.get("date") else None,
				'voucher_number': nro_comprobante,
				'type_op_det': type_op_det if type_op_det else "",
				'detraction_percent_id': detraction_percent_id.id if detraction_percent_id.id else False,
				})
			return move_search

		else:
			raise UserError(u'No se encontró el asiento: "%s" - "%s" - "%s" - "%s"' % (ruc,doc.code,serie+'-'+ref, self.journal_id.name))

	def find_type_document(self,code):
		catalog_payment_search = self.env['l10n_latam.document.type'].search([('code', '=', str(code))],limit=1)
		if catalog_payment_search:
			return catalog_payment_search
		else:
			raise Warning(_('No existe un Tipo de Comprobante con el Codigo "%s"') % code)

	def find_partner(self,code):
		partner_search = self.env['res.partner'].search([('vat', '=', str(code))],limit=1)
		if partner_search:
			return partner_search
		else:
			raise Warning(_('No existe un Partner con el RUC "%s"') % code)

	def download_template(self):
		return {
			 'type' : 'ir.actions.act_url',
			 'url': '/web/binary/download_template_import_doc_invoice_relac_example',
			 'target': 'new',
			 }

	def get_text_with_size(self,text,size,complement,right):
		if not text:
			text = ''
		if len(text)<size:
			digits_number = ('').join((size-len(text))*[complement])
			if right:
				out = text + digits_number
			else:
				out = digits_number + text
		elif len(text)>size:
			out = text[:size] if right else text[len(text)-size:]
		else:
			out = text

		return out