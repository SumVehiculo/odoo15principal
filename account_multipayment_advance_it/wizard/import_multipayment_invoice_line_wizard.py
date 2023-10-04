# -*- coding: utf-8 -*-

import time
from datetime import datetime
import tempfile
import binascii
import xlrd
from datetime import date, datetime
from odoo.exceptions import UserError
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

class ImportMultipaymentInvoiceLineWizard(models.TransientModel):
	_name = 'import.multipayment.invoice.line.wizard'

	multipayment_id = fields.Many2one('multipayment.advance.it',string='PM',required=True)
	document_file = fields.Binary(string='Excel')
	name_file = fields.Char(string='Nombre de Archivo')

	def importar(self):
		try:
			fp = tempfile.NamedTemporaryFile(delete= False,suffix=".xlsx")
			fp.write(binascii.a2b_base64(self.document_file))
			fp.seek(0)
			values = {}
			workbook = xlrd.open_workbook(fp.name)
			sheet = workbook.sheet_by_index(0)

		except:
			raise UserError("Archivo invalido!")

		for row_no in range(sheet.nrows):
			if row_no <= 0:
				continue
			else:
				line = list(map(lambda row:isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
				if len(line) == 5:
					values.update( {'partner_id': line[0],
								'type_document_id': line[1],
								'nro_comp': line[2],
								'account_id': line[3],
								'amount_currency':line[4],
								})
				elif len(line) > 5:
					raise UserError('Tu archivo tiene columnas mas columnas de lo esperado.')
				else:
					raise UserError('Tu archivo tiene columnas menos columnas de lo esperado.')

				self.create_invoice_line(values)

		return {'type': 'ir.actions.act_window_close'}

	def create_invoice_line(self,values):
		if values.get("account_id") == "":
			raise UserError('El campo de account_id no puede estar vacío.')
		if values.get("partner_id") == "":
			raise UserError('El campo de partner_id no puede estar vacío.')
		if values.get("type_document_id") == "":
			raise UserError('El campo de type_document_id no puede estar vacío.')
		if values.get("nro_comp") == "":
			raise UserError('El campo de nro_comp no puede estar vacío.')

		account_id = self.find_account(values.get("account_id"))
		partner_id = self.find_partner(values.get("partner_id"))
		type_document_id = self.find_type_document(values.get("type_document_id"))

		invoice_id = self.env['account.move.line'].search([('partner_id','=',partner_id.id),('type_document_id','=',type_document_id.id),
		('account_id','=',account_id.id),('nro_comp','=',values.get("nro_comp")),('company_id','=',self.multipayment_id.company_id.id)],limit=1)

		residual_amount = 0
		if invoice_id.currency_id:
			residual_amount = invoice_id.amount_residual_currency
		else:
			residual_amount = invoice_id.amount_residual

		line = self.env['multipayment.advance.it.line'].create({
			'partner_id': partner_id.id if partner_id else None,
			'tipo_documento':type_document_id.id if type_document_id else None,
			'invoice_id': invoice_id.id if invoice_id else None,
			'importe_divisa': values.get("amount_currency"),
			'main_id':self.multipayment_id.id,
			'saldo':residual_amount
		})
		line._update_debit_credit()
		return line
	
	def find_partner(self, name):
		partner_obj = self.env['res.partner']
		partner_search = partner_obj.search([('vat', '=', str(name))],limit=1)
		if partner_search:
			return partner_search
		else:
			raise UserError('No existe un Partner con el Nro de Documento "%s"'% name) 

	def find_account(self, code):
		account_obj = self.env['account.account']
		account_search = account_obj.search([('code', '=', str(code)),('company_id','=',self.env.company.id)],limit=1)
		if account_search:
			return account_search
		else:
			raise UserError('No existe una Cuenta con el Codigo "%s" en esta Compañia'% code)

	def find_type_document(self,code):
		catalog_payment_search = self.env['l10n_latam.document.type'].search([('code', '=', str(code))],limit=1)
		if catalog_payment_search:
			return catalog_payment_search
		else:
			raise UserError('No existe un Tipo de Comprobante con el Codigo "%s"'% code)

	def download_template(self):
		return {
			 'type' : 'ir.actions.act_url',
			 'url': '/web/binary/download_template_multipayment_invoice_line',
			 'target': 'new',
			 }