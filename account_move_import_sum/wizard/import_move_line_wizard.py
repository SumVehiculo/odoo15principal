# -*- coding: utf-8 -*-

import time
from datetime import datetime, timedelta
import tempfile
import binascii
import pytz
import xlrd
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

class ImportMoveLineWizard(models.TransientModel):
	_inherit = 'import.move.line.wizard'

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
				if len(line) == 18:
					date_string = None
					if line[9] != '':
						fecha_base = datetime(1900, 1, 1, tzinfo=pytz.timezone('UTC'))
						delta = timedelta(days=int(float(line[9]))-2)
						date_string = fecha_base + delta
					date_invoice_string = None
					if line[15] != '':
						fecha_base = datetime(1900, 1, 1, tzinfo=pytz.timezone('UTC'))
						delta = timedelta(days=int(float(line[15]))-2)
						date_invoice_string = fecha_base + delta
	  
					#Importar etiqueta analitica
		 
					id_etiqueta = []
					raw_invoice_tags=line[12].replace(" ","")
					raw_invoice_tags= raw_invoice_tags.split(',') if raw_invoice_tags else []
					tag_list= self.env['account.analytic.tag'].search([])
					for tag in tag_list:
						if str(tag.name).split()[0] in raw_invoice_tags:
							id_etiqueta.append(tag.id)
       
					#--------------------------------

	 
					values.update( {'account_id': line[0],
								'debit': line[1],
								'credit': line[2],
								'currency_id': line[3] if line[3] else 'PEN',
								'amount_currency':line[4],
								'tc':line[5],
								'partner_id':line[6],
								'type_document_id':line[7],
								'nro_comp':line[8],
								'date_maturity':date_string,
								'name':line[10],
								'analytic_account_id':line[11],
								'analytic_tag_ids':id_etiqueta,
								'amount_tax':line[13],
								'tag_ids':line[14],
								'invoice_date_it': date_invoice_string,
								'cta_cte': line[16] == 'SI',
								'work_order_id': line[17],
								})
				elif len(line) > 18:
					raise UserError('Tu archivo tiene columnas mas columnas de lo esperado.')
				else:
					raise UserError('Tu archivo tiene columnas menos columnas de lo esperado.')

				lineas.append(self.create_journal_entry_line(values))

		self.move_id.write({'line_ids': lineas})
		return {'type': 'ir.actions.act_window_close'}

	def create_journal_entry_line(self,values):
		if values.get("account_id") == "":
			raise UserError('El campo de account_id no puede estar vacío.')

		type_document_id = None
		partner_id = None
		analytic_account_id = None
		work_order_id = False

		if values.get("type_document_id"):
			s = str(values.get("type_document_id"))
			code_no = s.rstrip('0').rstrip('.') if '.' in s else s
			type_document_id = self.find_type_document(code_no)

		if values.get("partner_id"):
			s = str(values.get("partner_id"))
			vat = s.rstrip('0').rstrip('.') if '.' in s else s
			partner_id = self.find_partner(vat) if vat else None

		if values.get("analytic_account_id"):
			analytic_account_id = self.find_analytic_account(values.get("analytic_account_id"))

		
		if values.get("work_order_id"):
			work_order_id = self.find_work_order(values.get("work_order_id"))

		account_id = self.find_account(values.get("account_id"))

		tag_ids = []

		if values.get('tag_ids'):
			if str(values.get('tag_ids')) !="":
				tag_names = values.get('tag_ids').split(',')
				for name in tag_names:
					tag = self.env['account.account.tag'].search([('name', '=', name)])
					if not tag:
						raise UserError(' No existe la etiqueta de Cuenta "%s".'% name)
					tag_ids.append(tag.id)

		currency = self.env['res.currency'].search([('name','=',values.get("currency_id"))],limit=1)
		if currency.name != 'PEN':
			vals = (0,0,{
				'account_id': account_id.id if account_id else None,
				'partner_id': partner_id.id if partner_id else None,
				'type_document_id':type_document_id.id if type_document_id else None,
				'nro_comp': values.get("nro_comp"),
				'name': values.get("name"),
				'currency_id': currency.id,
				'amount_currency': float(values.get("amount_currency")) if values.get("amount_currency") else 0,
				'debit': float(values.get("debit")) if values.get("debit") else 0,
				'credit': float(values.get("credit")) if values.get("credit") else 0,
				'date_maturity':values.get("date_maturity"),
				'company_id': self.move_id.company_id.id,
				'tc': float(values.get("tc")) if values.get("tc") else 1,
				'analytic_account_id': analytic_account_id.id if analytic_account_id else None,
				'analytic_tag_ids': [(6, 0, values.get("analytic_tag_ids"))] if values.get("analytic_tag_ids") else False,
				'tax_amount_it': float(values.get("amount_tax")) if values.get("amount_tax") else 0,
				'tax_tag_ids':([(6,0,tag_ids)]),
				'invoice_date_it':values.get("invoice_date_it"),
				'cta_cte_origen':values.get("cta_cte"),
				'work_order_id': work_order_id
			})
			return vals
		else:
			vals = (0,0,{
				'account_id': account_id.id if account_id else None,
				'partner_id': partner_id.id if partner_id else None,
				'type_document_id':type_document_id.id if type_document_id else None,
				'nro_comp': values.get("nro_comp"),
				'name': values.get("name"),
				'debit': float(values.get("debit")) if values.get("debit") else 0,
				'credit': float(values.get("credit")) if values.get("credit") else 0,
				'date_maturity':values.get("date_maturity"),
				'company_id': self.move_id.company_id.id,
				'analytic_account_id': analytic_account_id.id if analytic_account_id else None,
				'analytic_tag_ids': [(6, 0, values.get("analytic_tag_ids"))] if values.get("analytic_tag_ids") else False,
				'tax_amount_it': float(values.get("amount_tax")) if values.get("amount_tax") else 0,
				'tax_tag_ids':([(6,0,tag_ids)]),
				'invoice_date_it':values.get("invoice_date_it"),
				'cta_cte_origen':values.get("cta_cte"),
				'work_order_id': work_order_id
			})
			return vals

	def find_work_order(self, name):
		work_order_id = self.env['project.project'].search([
      		('name', '=', name)
        ],limit=1)
		if not work_order_id:
			raise UserError(f'No se encontro la Orden de Trabajo "{name}".')
		return work_order_id.id