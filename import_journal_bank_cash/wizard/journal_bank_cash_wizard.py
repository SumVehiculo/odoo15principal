# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import api, fields, models, _
from datetime import datetime
from odoo.exceptions import UserError, AccessError
import csv
import base64
import io as StringIO
import xlrd
from odoo.tools import ustr
import logging


_logger = logging.getLogger(__name__)


class journal_bank_cash_wizard(models.TransientModel):
	_name = "journal.bank.cash.wizard"
	_description = "Asistente para importar Diarios Banco Y cajas"       

	import_type = fields.Selection([
		('csv', 'CSV File'),
		('excel', 'Excel File')
		], default="excel", string="Tipo de archivo", required=True)
	
	file = fields.Binary(string="Archivo")   

	
	def validate_field_value(self, field_name, field_ttype, field_value, field_required,field_name_m2o):
		""" Validate field value, depending on field type and given value """
		self.ensure_one()

		try:       
			checker = getattr(self, 'Archivo Invalido_' + field_ttype)
		except AttributeError:
			_logger.warning(field_ttype + ": Este tipo de campo no tiene método de validación")
			return {}
		else:
			return checker(field_name, field_ttype, field_value, field_required, field_name_m2o)    

	def show_success_msg(self):
		
		# to close the current active wizard        
		action = self.env.ref('import_journal_bank_cash.sh_journal_bank_cash_wizard_action').read()[0]
		action = {'type': 'ir.actions.act_window_close'} 
		
		# open the new success message box    
		#view = self.env.ref('sh_message.sh_message_wizard')
		#view_id = view and view.id or False                                   
		context = dict(self._context or {})
		dic_msg =  "Registros importados con éxito"
		
	
		context['message'] = dic_msg     

		return self.env['popup.it'].get_message(dic_msg)
	
	def import_pol_apply(self):		

			if self.import_type == 'excel':
				counter = 1
				skipped_line_no = {}
				row_field_dic = {}
				row_field_error_dic = {} 
				account_id =0             
				currency = None    
				type_journal,name,code = "","",""    
				#try:
				wb = xlrd.open_workbook(file_contents=base64.decodestring(self.file))
				sheet = wb.sheet_by_index(0)     
				skip_header = True    
				sequence_new = 0
				for row in range(sheet.nrows):
						if skip_header:
							skip_header = False
							continue

						if len(sheet.cell(row, 0).value)>5:
							raise UserError (u"El codigo corto no debe ser mayor que 5 caracteres")
						else:
							code = sheet.cell(row, 0).value
						if sheet.cell(row, 2).value in ['Banco','Efectivo']:
							if sheet.cell(row, 2).value == 'Banco':
								type_journal = 	'bank'
							if sheet.cell(row, 2).value == 'Efectivo':
								type_journal = 	'cash'
						else:
							raise UserError (u"No se puede crear un registro diferente del tipo BANCO o CAJA en el archivo excel.")

						account = self.env['account.account'].sudo().search([('code','=',str(sheet.cell(row, 4).value)),('company_id','=',self.env.company.id)],limit=1)
						if not account:
							raise UserError (u"La cuenta Contable " + str(sheet.cell(row, 4).value) + " No existe")
						else:
							account_id = account.id
						name=sheet.cell(row, 1).value
						currency=""
						if sheet.cell(row, 3).value != '':
							currency = self.env['res.currency'].sudo().search([('name','=',(sheet.cell(row, 3).value).strip())]).id
							if not currency:
								raise UserError ("No se encontro la moneda "+(sheet.cell(row, 3).value))
						diario=self.env['account.journal'].sudo().create({
								'code': code,
								'name': name,
								'type': type_journal,
								'currency_id': currency,
								'default_account_id': account_id,
								'company_id':self.env.company.id})
						if diario:
							counter += 1
							
						
				
				#except Exception:
				#	raise UserError(_("Lo sentimos, su archivo de Excel no coincide con nuestro formato"))
				 
				if counter > 1:					
					res = self.show_success_msg()
					return res


	def download_template(self):
		return {
			 'type' : 'ir.actions.act_url',
			 'url': '/web/binary/download_template_journal_bank_cash',
			 'target': 'new',
			 }
