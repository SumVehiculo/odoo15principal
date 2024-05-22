# -*- coding: utf-8 -*-

import tempfile
import binascii
import xlrd
from odoo.exceptions import UserError
from odoo import models, fields, exceptions, api, _
import base64

class ImportPartnerBankIt(models.TransientModel):
	_name = 'import.partner.bank.it'

	file = fields.Binary('Archivo')
	file_name = fields.Char()

	def import_partner(self):
		extension = ''
		if self.file:
			file_name = str(self.file_name)
			extension = file_name.split('.')[1]
		if extension not in ['xls','xlsx','XLS','XLSX']:
			raise UserError('Cargue solo el archivo xls o xlsx.!')
		fp = tempfile.NamedTemporaryFile(delete=False,suffix=".xlsx")
		fp.write(binascii.a2b_base64(self.file))
		fp.seek(0)
		values = {}
		res = {}
		workbook = xlrd.open_workbook(fp.name)
		sheet = workbook.sheet_by_index(0)
		for row_no in range(sheet.nrows):
			if row_no <= 0:
				fields = map(lambda row:row.value.encode('utf-8'), sheet.row(row_no))
			else:
				line = list(map(lambda row:isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
				values.update( {'ruc':line[0],
								'account_number': line[1],
								'bank': line[2],
								'currency': line[3],
								'detrac': line[4],
								'name': line[5]
								})
				res = self.create_partner(values)
		
		return self.env['popup.it'].get_message('SE IMPORTARON LAS CUENTAS BANCARIAS DE MANERA CORRECTA.')
	
	def create_partner(self, values):
		if str(values.get('ruc')) == '':
			raise UserError(u'Es necesario establecer el titular.')
		if str(values.get('account_number')) == '':
			raise UserError(u'Es necesario establecer el Número de Cuenta.')
		currency_id = bank_id = None

		if str(values.get('currency')) != '':
			currency_id = self.env['res.currency'].search([('name','=',values.get('currency'))],limit=1).id
			if not currency_id:
				raise UserError(u'No existe la moneda establecida.')
		if str(values.get('bank')) != '':
			bank_id = self.env['res.bank'].search([('name','=',values.get('bank'))],limit=1).id
			if not bank_id:
				raise UserError(u'No existe el banco establecido.')
			
		is_detrac = False
		if ((values.get('detrac')) == 'SI'):
			is_detrac = True

		s = str(values.get("ruc"))
		vat = s.rstrip('0').rstrip('.') if '.' in s else s
		partner_id = self.find_partner(vat)
		
		account_number = str(values.get("account_number"))
		acc_number = account_number.rstrip('0').rstrip('.') if '.' in account_number else account_number
		
		vals = {
				'acc_number':acc_number,
				'partner_id':partner_id.id,
				'bank_id':bank_id,
				'currency_id':currency_id,
				'is_detraction_account':is_detrac,
				'acc_holder_name':values.get("name"),
				'company_id':self.env.company.id
				}
		res = self.env['res.partner.bank'].create(vals)
		return res
		
	def find_partner(self, name):
		partner_obj = self.env['res.partner']
		partner_search = partner_obj.search([('vat', '=', str(name))],limit=1)
		if partner_search:
			return partner_search
		else:
			raise UserError('No existe un Partner con el Nro de Documento "%s"' % name)

	def download_template(self):
		return {
			 'type' : 'ir.actions.act_url',
			 'url': '/web/binary/download_partner_bank_import_template',
			 'target': 'new',
			 }