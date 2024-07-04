# -*- coding: utf-8 -*-
import tempfile
import binascii
import xlrd
from datetime import  datetime
from odoo import models, _
from odoo.exceptions import UserError


class ImportInvoiceIt(models.Model):
	_inherit = "import.invoice.it"
	
	def make_invoice_line(self, values, inv_id):
		product_obj = self.env['product.product']

		if self.import_prod_option == 'barcode':
			product_id = product_obj.search([('barcode',  '=',values['product'])],limit=1)
		elif self.import_prod_option == 'code':
			product_id = product_obj.search([('default_code', '=',values['product'])],limit=1)
		else:
			product_id = product_obj.search([('name', '=',values['product'])],limit=1)

		product_uom = self.env['uom.uom'].search([('name', '=', values.get('uom'))],limit=1)
		if not product_uom:
			raise UserError(_(' "%s" Product UOM category is not available.') % values.get('uom'))

		tax_ids = []
		if inv_id.move_type == 'out_invoice':
			if values.get('tax'):
				if ';' in  values.get('tax'):
					tax_names = values.get('tax').split(';')
					for name in tax_names:
						tax= self.env['account.tax'].search([('name', '=', name),('type_tax_use','=','sale')])
						if not tax:
							raise UserError(_('"%s" Tax not in your system') % name)
						tax_ids.append(tax.id)

				elif ',' in  values.get('tax'):
					tax_names = values.get('tax').split(',')
					for name in tax_names:
						tax= self.env['account.tax'].search([('name', '=', name),('type_tax_use','=','sale')])
						if not tax:
							raise UserError(_('"%s" Tax not in your system') % name)
						tax_ids.append(tax.id)
				else:
					tax_names = values.get('tax')
					tax= self.env['account.tax'].search([('name', '=', tax_names),('type_tax_use','=','sale')])
					if not tax:
						raise UserError(_('"%s" Tax not in your system') % tax_names)
					tax_ids.append(tax.id)
		elif inv_id.move_type == 'in_invoice':
			if values.get('tax'):
				if ';' in values.get('tax'):
					tax_names = values.get('tax').split(';')
					for name in tax_names:
						tax = self.env['account.tax'].search([('name', '=', name), ('type_tax_use', '=', 'purchase')])
						if not tax:
							raise UserError(_('"%s" Tax not in your system') % name)
						tax_ids.append(tax.id)

				elif ',' in values.get('tax'):
					tax_names = values.get('tax').split(',')
					for name in tax_names:
						tax = self.env['account.tax'].search([('name', '=', name), ('type_tax_use', '=', 'purchase')])
						if not tax:
							raise UserError(_('"%s" Tax not in your system') % name)
						tax_ids.append(tax.id)
				else:
					tax_names = values.get('tax')
					tax = self.env['account.tax'].search([('name', '=', tax_names), ('type_tax_use', '=', 'purchase')])
					if not tax:
						raise UserError(_('"%s" Tax not in your system') % tax_names)
					tax_ids.append(tax.id)
		elif inv_id.move_type == 'out_refund':
			if values.get('tax'):
				if ';' in  values.get('tax'):
					tax_names = values.get('tax').split(';')
					for name in tax_names:
						tax= self.env['account.tax'].search([('name', '=', name),('type_tax_use','=','sale')])
						if not tax:
							raise UserError(_('"%s" Tax not in your system') % name)
						tax_ids.append(tax.id)

				elif ',' in  values.get('tax'):
					tax_names = values.get('tax').split(',')
					for name in tax_names:
						tax= self.env['account.tax'].search([('name', '=', name),('type_tax_use','=','sale')])
						if not tax:
							raise UserError(_('"%s" Tax not in your system') % name)
						tax_ids.append(tax.id)
				else:
					tax_names = values.get('tax')
					tax= self.env['account.tax'].search([('name', '=', tax_names),('type_tax_use','=','sale')])
					if not tax:
						raise UserError(_('"%s" Tax not in your system') % tax_names)
					tax_ids.append(tax.id)
		else:
			if values.get('tax'):
				if ';' in values.get('tax'):
					tax_names = values.get('tax').split(';')
					for name in tax_names:
						tax = self.env['account.tax'].search([('name', '=', name), ('type_tax_use', '=', 'purchase')])
						if not tax:
							raise UserError(_('"%s" Tax not in your system') % name)
						tax_ids.append(tax.id)

				elif ',' in values.get('tax'):
					tax_names = values.get('tax').split(',')
					for name in tax_names:
						tax = self.env['account.tax'].search([('name', '=', name), ('type_tax_use', '=', 'purchase')])
						if not tax:
							raise UserError(_('"%s" Tax not in your system') % name)
						tax_ids.append(tax.id)
				else:
					tax_names = values.get('tax')
					tax = self.env['account.tax'].search([('name', '=', tax_names), ('type_tax_use', '=', 'purchase')])
					if not tax:
						raise UserError(_('"%s" Tax not in your system') % tax_names)
					tax_ids.append(tax.id)

		if self.account_opt == 'default':
			if inv_id.move_type == 'out_invoice':
				if product_id and product_id.property_account_income_id:
					account = product_id.property_account_income_id
				elif product_id and product_id.categ_id.property_account_income_categ_id:
					account = product_id.categ_id.property_account_income_categ_id
				else:
					account_search = self.env['ir.property'].search([('name', '=', 'property_account_income_categ_id'),('company_id','=',self.company_id.id)],limit=1)
					account = account_search.value_reference
					account = account.split(",")[1]
					account = self.env['account.account'].browse(account)
			if inv_id.move_type == 'in_invoice':
				if product_id and product_id.property_account_expense_id:
					account = product_id.property_account_expense_id
				elif product_id and product_id.categ_id.property_account_expense_categ_id:
					account = product_id.categ_id.property_account_expense_categ_id
				else:
					account_search = self.env['ir.property'].search([('name', '=', 'property_account_expense_categ_id'),('company_id','=',self.company_id.id)],limit=1)
					account = account_search.value_reference
					account = account.split(",")[1]
					account = self.env['account.account'].browse(account)

			if inv_id.move_type == 'out_refund':
				if product_id and product_id.property_account_income_id:
					account = product_id.property_account_income_id
				elif product_id and product_id.categ_id.property_account_income_categ_id:
					account = product_id.categ_id.property_account_income_categ_id
				else:
					account_search = self.env['ir.property'].search([('name', '=', 'property_account_income_categ_id'),('company_id','=',self.company_id.id)],limit=1)
					account = account_search.value_reference
					account = account.split(",")[1]
					account = self.env['account.account'].browse(account)
			if inv_id.move_type == 'in_refund':
				if product_id and product_id.property_account_expense_id:
					account = product_id.property_account_expense_id
				elif product_id and product_id.categ_id.property_account_expense_categ_id:
					account = product_id.categ_id.property_account_expense_categ_id
				else:
					account_search = self.env['ir.property'].search([('name', '=', 'property_account_expense_categ_id'),('company_id','=',self.company_id.id)],limit=1)
					account = account_search.value_reference
					account = account.split(",")[1]
					account = self.env['account.account'].browse(account)

		else:
			if values.get('account') == '':
				raise UserError(_(' You can not left blank account field if you select Excel Account Option'))
			else:
				s = str(values.get("account"))
				accc = s.rstrip('0').rstrip('.') if '.' in s else s
				account_id = self.env['account.account'].search([('code','=',accc),('company_id','=',self.company_id.id)])
				if account_id:
					account = account_id
				else:
					raise UserError(_(' "%s" Account is not available.') % accc) 

		analytic_account_id = False
		if values.get("analytic_account_id"):
			analytic_account_id = self.find_analytic_account(values.get("analytic_account_id"))

		work_order_id = False
		if values.get("work_order_id"):
			work_order_id = self.find_work_order(values.get("work_order_id"))
   
		vals = {
			'product_id' : product_id.id if product_id else None,
			'quantity' : float(values.get('quantity')),
			'price_unit' : float(values.get('price')),
			'discount':float(values.get('discount')),
			'name' : values.get('description'),
			'account_id' : account.id,
			'analytic_account_id': analytic_account_id.id if analytic_account_id else None,
			'product_uom_id' : product_uom.id,
			'company_id' : self.company_id.id,
			'l10n_latam_document_type_id': inv_id.l10n_latam_document_type_id.id,
			'work_order_id': work_order_id
		}
		if tax_ids:
			vals.update({'tax_ids':([(6,0,tax_ids)])})

		inv_id.write({'invoice_line_ids' :([(0,0,vals)]) })
		inv_id.write({'import_invoice_it_id': self.id})    
		
		return inv_id

	
	def find_work_order(self, name):
		work_order_id = self.env['project.project'].search([
      		('name', '=', name)
        ],limit=1)
		if not work_order_id:
			raise UserError(f'No se encontro la Orden de Trabajo "{name}".')
		return work_order_id
	
	def import_invoice(self):
		if not self.type_import:
			raise UserError('Falta escoger Tipo')
		if not self.account_opt:
			raise UserError('Falta escoger "Cuenta de" en pestaña Cuenta')
		if not self.journal_id:
			raise UserError('Falta escoger "Diario" para la importación')
		try:
			fp = tempfile.NamedTemporaryFile(delete= False,suffix=".xlsx")
			fp.write(binascii.a2b_base64(self.file))
			fp.seek(0)
			values = {}
			invoice_ids=[]
			workbook = xlrd.open_workbook(fp.name)
			sheet = workbook.sheet_by_index(0)
		except Exception:
			raise UserError(_("Please select an XLS file or You have selected invalid file"))
		
  		#NUEVA FUNCIONALIDAD
		partner = []
		for row_vali in range(sheet.nrows):			
			if row_vali <= 0:
				continue
			else:
				valid = list(map(lambda row:isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value), sheet.row(row_vali)))
				partner_obj = self.env['res.partner']
				
				if str(valid[1]):
					s=str(valid[1])
					vat = s.rstrip('0').rstrip('.') if '.' in s else s
					partner_search = partner_obj.search([('vat', '=', str(vat)),('parent_id','=',False)],limit=1)
					if not partner_search:
						partner.append(vat)
		if partner:
			return self.get_excel_not_partner(partner)

		for row_no in range(sheet.nrows):
			val = {}
			if row_no <= 0:
				continue
			else:
				line = list(map(lambda row:isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
				if self.account_opt == 'default':
					if len(line) == 32:
						if line[11] == '':
							raise UserError(_('Please assign a date'))
						else:
							a1 = int(float(line[11]))
							a1_as_datetime = datetime(*xlrd.xldate_as_tuple(a1, workbook.datemode))
							date_string = a1_as_datetime.date().strftime('%Y-%m-%d')
						if line[12] == '':
							raise UserError(_('Please assign a invoice date'))
						else:
							a1_i = int(float(line[12]))
							a1_as_datetime_i = datetime(*xlrd.xldate_as_tuple(a1_i, workbook.datemode))
							date_invoice_string = a1_as_datetime_i.date().strftime('%Y-%m-%d')
						date_invoice_due_string = date_invoice_string
						if line[17] != '':
							a1_i = int(float(line[17]))
							a1_as_datetime_i = datetime(*xlrd.xldate_as_tuple(a1_i, workbook.datemode))
							date_invoice_due_string = a1_as_datetime_i.date().strftime('%Y-%m-%d')
						fecha_doc_relac = None
						if line[19] != '':
							a1_i = int(float(line[19]))
							a1_as_datetime_i = datetime(*xlrd.xldate_as_tuple(a1_i, workbook.datemode))
							fecha_doc_relac = a1_as_datetime_i.date().strftime('%Y-%m-%d')
						fecha_detrac = None
						if line[26] != '':
							a1_i = int(float(line[26]))
							a1_as_datetime_i = datetime(*xlrd.xldate_as_tuple(a1_i, workbook.datemode))
							fecha_detrac = a1_as_datetime_i.date().strftime('%Y-%m-%d')

						values.update( {'invoice':line[0],
										'customer': str(line[1]),
										'currency': line[2],
										'product': line[3].split('.')[0],
										'quantity': line[4],
										'uom': line[5],
										'description': line[6],
										'price': line[7],
										'discount':line[8],
										'salesperson': line[9],
										'tax': line[10],
										'date': date_string,
										'date_invoice': date_invoice_string,
										'date_invoice_due': date_invoice_due_string,
										'seq_opt':self.sequence_opt,
										'td': str(line[13]),
										'nro_comprobante': str(line[14]),
										'glosa': str(line[15]),
										'analytic_account_id': str(line[16]),
										'td_doc_relac': str(line[18]),
										'fecha_doc_relac': fecha_doc_relac,
										'nro_doc_relac': str(line[20]),
										'monto_me_doc_relac': str(line[21]),
										'total_mn_doc_relac': str(line[22]),
										'base_doc_relac': str(line[23]),
										'igv_doc_relac': str(line[24]),
										'tipo_ope': str(line[25]),
										'fecha_detrac': fecha_detrac,
										'nro_comp_detrac': str(line[27]),
										'monto_detrac': line[28],
										'bien_servi': str(line[29]),
										'tc': line[30],
										'work_order_id':str(line[31])
										})
					elif len(line) > 32:
						raise UserError(u'Tu archivo tiene más columnas que la plantilla de ejemplo.')
					else:
						raise UserError(u'Tu archivo tiene menos columnas que la plantilla de ejemplo.')
				else:
					if len(line) == 33:
						if line[12] == '':
							raise UserError(_('Please assign a date'))
						else:
							a1 = int(float(line[12]))
							a1_as_datetime = datetime(*xlrd.xldate_as_tuple(a1, workbook.datemode))
							date_string = a1_as_datetime.date().strftime('%Y-%m-%d')

						if line[13] == '':
							raise UserError(_('Please assign a invoice date'))
						else:
							a1_i = int(float(line[13]))
							a1_as_datetime_i = datetime(*xlrd.xldate_as_tuple(a1_i, workbook.datemode))
							date_invoice_string = a1_as_datetime_i.date().strftime('%Y-%m-%d')
						date_invoice_due_string = date_invoice_string
						if line[18] != '':
							a1_i = int(float(line[18]))
							a1_as_datetime_i = datetime(*xlrd.xldate_as_tuple(a1_i, workbook.datemode))
							date_invoice_due_string = a1_as_datetime_i.date().strftime('%Y-%m-%d')
						fecha_doc_relac = None
						if line[20] != '':
							a1_i = int(float(line[20]))
							a1_as_datetime_i = datetime(*xlrd.xldate_as_tuple(a1_i, workbook.datemode))
							fecha_doc_relac = a1_as_datetime_i.date().strftime('%Y-%m-%d')
						fecha_detrac = None
						if line[27] != '':
							a1_i = int(float(line[27]))
							a1_as_datetime_i = datetime(*xlrd.xldate_as_tuple(a1_i, workbook.datemode))
							fecha_detrac = a1_as_datetime_i.date().strftime('%Y-%m-%d')
						values.update( {'invoice':line[0],
										'customer': str(line[1]),
										'currency': line[2],
										'product': line[3].split('.')[0],
										'account': line[4],
										'quantity': line[5],
										'uom': line[6],
										'description': line[7],
										'price': line[8],
										'discount':line[9],
										'salesperson': line[10],
										'tax': line[11],
										'date': date_string,
										'date_invoice': date_invoice_string,
										'date_invoice_due': date_invoice_due_string,
										'seq_opt':self.sequence_opt,
										'td': str(line[14]),
										'nro_comprobante': str(line[15]),
										'glosa': str(line[16]),
										'analytic_account_id': str(line[17]),
										'td_doc_relac': str(line[19]),
										'fecha_doc_relac': fecha_doc_relac,
										'nro_doc_relac': str(line[21]),
										'monto_me_doc_relac': str(line[22]),
										'total_mn_doc_relac': str(line[23]),
										'base_doc_relac': str(line[24]),
										'igv_doc_relac': str(line[25]),
										'tipo_ope': str(line[26]),
										'fecha_detrac': fecha_detrac,
										'nro_comp_detrac': str(line[28]),
										'monto_detrac': line[29],
										'bien_servi': str(line[30]),
										'tc': line[31],
          								'work_order_id': str(line[32]),
										})
					elif len(line) > 33:
						raise UserError(u'Tu archivo tiene más columnas que la plantilla de ejemplo.')
					else:
						raise UserError(u'Tu archivo tiene menos columnas que la plantilla de ejemplo.')
				res = self.make_invoice(values)
				res._onchange_tc_per()
				res._compute_amount()
				res.flush()
				if date_string != date_invoice_string:
					res.write({'date': date_string})
				invoice_ids.append(res)

		if self.stage == 'confirm':
			for res in invoice_ids: 
				if res.state in ['draft']:
					res.action_post()
		for invoice in self.move_ids:
			invoice.invoice_name = None
		self.state = 'import'
	