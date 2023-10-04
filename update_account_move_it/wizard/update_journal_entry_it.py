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

class UpdateJournalEntryIt(models.TransientModel):
	_name = 'update.journal.entry.it'
	_description = 'Update Journal Entry It'

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
				if len(line) == 11:
					date_string = None
					if line[4] != '':
						a1 = int(float(line[4]))
						a1_as_datetime = datetime(*xlrd.xldate_as_tuple(a1, workbook.datemode))
						date_string = a1_as_datetime.date().strftime('%Y-%m-%d')
					values = ({'journal_id':line[0],
								'asiento_nro':line[1],
								'suj_a_detra': line[2],
								'tipo_opera': str(line[3]),
								'fecha_det': date_string,
								'cod_opera': str(line[5]),
								'nro_comp_det':line[6],
								'monto_det':line[7],
								'suj_a_per': line[8],
								'tipo_tasa_per': line[9],
								'nro_per': line[10],
								})
				elif len(line) > 11:
					raise Warning(_('Tu archivo tiene columnas mas columnas de lo esperado.'))
				else:
					raise Warning(_('Tu archivo tiene columnas menos columnas de lo esperado.'))
				
				res = self.update_move(values)
				move_ids.append(res)

		for res in move_ids: 
			if res.state in ['draft']:
				res.post()

		return self.env['popup.it'].get_message(u'SE ACTUALIZARON CON EXITO LOS ASIENTOS.')

	def update_move(self, values):
		move_obj = self.env['account.move']

		if str(values.get('asiento_nro')) == '':
			raise Warning(_('El campo "asiento_nro" no puede estar vacio.'))
		if str(values.get('journal_id')) == '':
			raise Warning(_('El campo "journal_id" no puede estar vacio.'))

		s = str(values.get("journal_id"))
		code = s.rstrip('0').rstrip('.') if '.' in s else s
		journal_id = self.find_journal(code)

		move_search = move_obj.search([
					('name', '=', values.get('asiento_nro')),
					('journal_id','=',journal_id.id),
					('company_id','=',self.env.company.id)
				],limit=1)
		
		suj_det, suj_per = False, False
		if values.get("suj_a_detra") == 'TRUE':
			suj_det = True
		if values.get("suj_a_per") == 'TRUE':
			suj_per = True
		
		detraction_percent_id = None
		if str(values.get('cod_opera')) != '':
			detraction_percent_id = self.find_detractions_percent(str(values.get('cod_opera')))

		if move_search:
			move_search.write({
				'linked_to_detractions': suj_det,
				'type_op_det': values.get("tipo_opera") if values.get("tipo_opera") else '',
				'date_detraccion': values.get("fecha_det") if values.get("fecha_det") else None,
				'detraction_percent_id': detraction_percent_id,
				'voucher_number': values.get("nro_comp_det") if values.get("nro_comp_det") else '',
				'detra_amount': values.get("monto_det") if values.get("monto_det") else 0,
				'linked_to_perception': suj_per,
				'type_t_perception': values.get("tipo_tasa_per") if values.get("tipo_tasa_per") else '',
				'number_perception': values.get("nro_per") if values.get("nro_per") else ''
				})
			return move_search

		else:
			raise UserError(u'No se encontró el asiento con el numero "%s" y el diario "%s"' % (values.get('asiento_nro'),values.get("journal_id")))

	def find_journal(self,code):
		journal_search = self.env['account.journal'].search([('code','=',code),('company_id','=',self.env.company.id)],limit=1)
		if journal_search:
			return journal_search
		else:
			raise UserError(_('No existe el diario "%s" en la Compañia.') % code)
	
	def find_detractions_percent(self,code):
		detraciont_search = self.env['detractions.catalog.percent'].search([('code','=',code)],limit=1)
		if detraciont_search:
			return detraciont_search.id
		else:
			raise UserError(_(u'No existe el procentaje de Detraccion con el código "%s" en la Compañia.') % code)

	def download_template(self):
		return {
			 'type' : 'ir.actions.act_url',
			 'url': '/web/binary/download_template_update_journal_entry_example',
			 'target': 'new',
			 }