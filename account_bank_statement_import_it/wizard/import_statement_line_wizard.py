# -*- coding: utf-8 -*-

import time
from datetime import datetime, timedelta
import tempfile
import binascii
import xlrd
from odoo.exceptions import UserError
from dateutil import parser
import pytz
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

class ImportStatementLineWizard(models.TransientModel):
	_name = 'import.statement.line.wizard'
	_description = 'Import Statement Line Wizard'

	statement_id = fields.Many2one('account.bank.statement',string='Extracto',required=True)
	document_file = fields.Binary(string='Excel', help="El archivo Excel debe ir con la cabecera: date, name, partner_id, ref, catalog_payment_id, amount")
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

		lineas = []

		for row_no in range(sheet.nrows):
			if row_no <= 0:
				continue
			else:
				line = list(map(lambda row:isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
				if len(line) == 8:
					date_format=None
					if line[0] == '':
						raise UserError('Por favor ingresa el campo Fecha')
					else:
						date_format = self.convert_date(line[0])
					ref = ''
					if line[2] != '':
						texto = line[2]
						partes = texto.split(".")
						ref = partes[0]		
					values.update( {'date': date_format,
								'payment_ref': line[1],
								'ref': ref,
								'partner_id': line[3],
								'type_document_id': line[4],
								'catalog_payment_id': line[5],
								'amount': line[6],
								'cash_flow_id': line[7],
								})
				elif len(line) > 8:
					raise UserError('Tu archivo tiene columnas mas columnas de lo esperado.')
				else:
					raise UserError('Tu archivo tiene columnas menos columnas de lo esperado.')

				lineas.append(self.create_lines_statement(values))
			
		self.statement_id.write({'line_ids': lineas})
		return {'type': 'ir.actions.act_window_close'}

	def create_lines_statement(self,values):
		if values.get("payment_ref") == "":
			raise UserError(u'El "Descripción" de name no puede estar vacío.')

		catalog_payment_id = None
		partner_id = None
		type_document_id = None
		cash_flow_id = None

		if values.get("catalog_payment_id"):
			s = str(values.get("catalog_payment_id"))
			code_no = s.rstrip('0').rstrip('.') if '.' in s else s
			catalog_payment_id = self.find_catalog_payment(code_no) if code_no else None

		if values.get("partner_id"):
			s = str(values.get("partner_id"))
			vat = s.rstrip('0').rstrip('.') if '.' in s else s
			partner_id = self.find_partner(vat) if vat else None
		
		if values.get("type_document_id"):
			s = str(values.get("type_document_id"))
			code = s.rstrip('0').rstrip('.') if '.' in s else s
			type_document_id = self.find_type_document(code)
		
		if values.get("cash_flow_id"):
			cash_flow_id = self.find_cash_flow(values.get('cash_flow_id'))

		vals = (0,0,{
			'date': values.get("date"),
			'payment_ref': values.get("payment_ref"),
			'type_document_id': type_document_id.id if type_document_id else None,
			'partner_id': partner_id.id if partner_id else None,
			'ref': values.get("ref"),
			'catalog_payment_id':catalog_payment_id.id if catalog_payment_id else None,
			'amount': values.get("amount"),
			'account_cash_flow_id': cash_flow_id.id if cash_flow_id else None,
			'company_id': self.statement_id.company_id.id,
		})
		return vals

	def find_partner(self, name):
		partner_obj = self.env['res.partner']
		partner_search = partner_obj.search([('vat', '=', str(name))],limit=1)
		if partner_search:
			return partner_search
		else:
			raise UserError('No existe un Partner con el Nro de Documento "%s"' % name)

	def find_catalog_payment(self,code):
		catalog_payment_search = self.env['einvoice.catalog.payment'].search([('code', '=', str(code))],limit=1)
		if catalog_payment_search:
			return catalog_payment_search
		else:
			raise UserError('No existe un Medio de Pago con el Codigo "%s"' % code)
	
	def find_type_document(self,code):
		catalog_payment_search = self.env['l10n_latam.document.type'].search([('code', '=', str(code))],limit=1)
		if catalog_payment_search:
			return catalog_payment_search
		else:
			raise UserError('No existe un Tipo de Comprobante con el Codigo "%s"' % code)
	
	def find_cash_flow(self, code):
		cash_flow_obj = self.env['account.cash.flow']
		cash_flow_search = cash_flow_obj.search([('code', '=', code)],limit=1)
		if cash_flow_search:
			return cash_flow_search
		else:
			raise UserError('"%s" Flujo de Caja no disponible.' % code)

	def download_template(self):
		return {
			 'type' : 'ir.actions.act_url',
			 'url': '/web/binary/download_template_statement_line',
			 'target': 'new',
			 }
	
	def convert_date(self, date):
		try:
			numeric_date = float(str(date))
			seconds = (numeric_date - 25569) * 86400.0
			d = datetime.utcfromtimestamp(seconds)
			return d.strftime('%Y-%m-%d')  
		except ValueError:
			for fmt in ("%d-%m-%Y", "%Y/%m/%d", "%b %d, %Y", "%d %B %Y","%d/%m/%Y"):
				try:
					return datetime.strptime(str(date), fmt).strftime("%Y-%m-%d")
				except ValueError:
					continue
			raise UserError(f"Formato no reconocido para la fecha: {str(date)}")
	