# -*- coding: utf-8 -*-

from datetime import *
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import requests
import tempfile
import binascii
import xlrd
from odoo.exceptions import Warning, UserError

import requests
import json

class ImportCurrencyRateWizard(models.TransientModel):
	_name = "import.currency.rate.wizard"
	_description = 'Import Currency Rate Wizard'
	
	name_file = fields.Char(string='Nombre de Archivo')
	file = fields.Binary('File')
	company_id = fields.Many2one('res.company',string=u'Compañía',default=lambda self: self.env.company)

	def importar(self):
		if not self.file:
			raise UserError('Tiene que cargar un archivo.')
		
		try:
			fp = tempfile.NamedTemporaryFile(delete= False,suffix=".xlsx")
			fp.write(binascii.a2b_base64(self.file))
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
				if len(line) == 4:
					date_string = None
					if line[1] != '':
						a1 = int(float(line[1]))
						a1_as_datetime = datetime(*xlrd.xldate_as_tuple(a1, workbook.datemode))
						date_string = a1_as_datetime.date().strftime('%Y-%m-%d')
					values = ({'currency':line[0],
								'date':date_string,
								'sale_type':float(line[2]),
								'purchase_type': float(line[3]),
								})
				elif len(line) > 4:
					raise Warning(_('Tu archivo tiene columnas mas columnas de lo esperado.'))
				else:
					raise Warning(_('Tu archivo tiene columnas menos columnas de lo esperado.'))
				
				self.make_currency_rate(values)

		return self.env['popup.it'].get_message(u'SE IMPORTARON EXITOSAMENTE LOS TIPOS DE CAMBIO.')

	def make_currency_rate(self, values):
		rate_obj = self.env['res.currency.rate']
		currency = self.find_currency(values.get('currency'))
		if currency:
			if not values.get('date'):
				raise Warning(_('El campo "date" no puede estar vacio.'))

			rate_search = rate_obj.search([
						('name', '=', values.get('date')),
						('currency_id', '=', currency.id),
						('company_id','=',self.company_id.id)
					],limit=1)

			if rate_search:
				rate_search.write({
					'rate': 1/values.get('sale_type'),
					'sale_type': values.get('sale_type'),
					'purchase_type': values.get('purchase_type'),
				})
			else:
				rate_obj.create({
					'currency_id': currency.id,
					'rate': 1/values.get('sale_type'),
					'name': values.get('date'),
					'sale_type': values.get('sale_type'),
					'purchase_type': values.get('purchase_type'),
					'company_id': self.company_id.id
				})
	
	def find_currency(self, name):
		currency_obj = self.env['res.currency']
		currency_search = currency_obj.search([('name', '=', name)],limit=1)
		if currency_search:
			return currency_search
		else:
			raise UserError(_(' "%s" Currency are not available.') % name)
	
	def download_template(self):
		return {
			 'type' : 'ir.actions.act_url',
			 'url': '/web/binary/download_template_currency_rate_import',
			 'target': 'new',
			 }