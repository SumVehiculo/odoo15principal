# -*- coding: utf-8 -*-

import tempfile
import binascii
import xlrd
from datetime import date, datetime
from odoo.exceptions import UserError
from odoo import models, fields, api, _
import base64

class ImportInvoiceIt(models.Model):
	_name = "import.invoice.it"

	name = fields.Char(string=u'Nombre')
	name_file = fields.Char(string='Nombre de Archivo')
	file = fields.Binary('File')
	account_opt = fields.Selection([('default', 'Usar Cuenta Configurada en Producto'), ('custom', 'Usar Cuenta de Excel')], string='Cuenta de',default='default', required=True)
	type_import = fields.Selection([('out_invoice', 'Cliente'), ('in_invoice', 'Proveedor'),('out_refund',u'Nota Crédito Cliente'),('in_refund',u'Nota Crédito Proveedor')], string='Tipo', required=True, default='in_invoice')
	sequence_opt = fields.Selection([('custom', 'Usar secuencia de Excel'), ('system', 'Usar secuencia por defecto del Sistema')], string='Secuencia de',default='custom')
	stage = fields.Selection(
		[('draft', 'Importar Factura en Borrador'), ('confirm', u'Validar Factura automáticamente')],
		string="Estado de Factura", default='draft')
	import_prod_option = fields.Selection([('name', 'Nombre'),('code', 'Referencia Interna'),('barcode', 'Barcode')],string='Importar Producto por',default='name')
	journal_id = fields.Many2one('account.journal',string='Diario')
	state = fields.Selection([('draft','Borrador'),('import','Importado'),('cancel','Cancelado')],string='Estado',default='draft')
	move_ids = fields.One2many('account.move','import_invoice_it_id',string='Facturas')
	company_id = fields.Many2one('res.company',string=u'Compañía',default=lambda self: self.env.company)

	@api.model
	def create(self,vals):
		id_seq = self.env['ir.sequence'].search([('name','=','Importaciones Facturas'),('company_id','=',self.env.company.id)], limit=1)
		if not id_seq:
			if not id_seq:
				id_seq = self.env['ir.sequence'].create({'name':'Importaciones Facturas',
				'implementation':'no_gap',
				'active':True,
				'prefix':'IMF-',
				'padding':5,
				'number_increment':1,
				'number_next_actual' :1,
				'company_id':self.env.company.id})

		vals['name'] = id_seq._next()
		t = super(ImportInvoiceIt,self).create(vals)
		return t

	def unlink(self):
		if self.state != 'draft':
			raise UserError('No se puede eliminar una importacion en proceso.')
		t = super(ImportInvoiceIt,self).unlink()
		return t

	def open_entries(self):
		self.ensure_one()
		action = self.env.ref('account.action_move_journal_line').read()[0]
		domain = [('id', 'in', self.move_ids.ids)]
		context = dict(self.env.context, default_invoice_id=self.id)
		views = [(self.env.ref('account.view_move_tree').id, 'tree'), (False, 'form'), (False, 'kanban')]
		return dict(action, domain=domain, context=context, views=views)

	def open_line_entries(self):
		self.ensure_one()
		action = self.env.ref('account.action_account_moves_all').read()[0]
		domain = [('id', 'in', self.move_ids.line_ids.ids)]
		context = dict(self.env.context, default_invoice_id=self.id)
		views = [(self.env.ref('account.view_move_line_tree').id, 'tree'), (False, 'form'), (False, 'kanban')]
		return dict(action, domain=domain, context=context, views=views)

	def make_invoice(self, values):
		invoice_obj = self.env['account.move']
		if self.sequence_opt == "custom":
			invoice_search = invoice_obj.search([
				('name', '=', values.get('invoice')),
				('move_type', '=', self.type_import),
				('custom_seq','=',True),
				('journal_id','=',self.journal_id.id),
				('company_id','=',self.company_id.id)
			],limit=1)
		else:
			invoice_search = invoice_obj.search([
				('invoice_name', '=', values.get('invoice')),
				('move_type', '=', self.type_import),
				('system_seq','=',True),
				('journal_id','=',self.journal_id.id),
				('company_id','=',self.company_id.id)
			],limit=1)
			
		if invoice_search:
			s = str(values.get("customer"))
			vat = s.rstrip('0').rstrip('.') if '.' in s else s
			if invoice_search.partner_id.vat != vat:
				raise UserError(_('Customer name is different for "%s" .\n Please define same.') % vat)

			if  invoice_search.currency_id.name != values.get('currency'):
				raise UserError(_('Currency is different for "%s" .\n Please define same.') % values.get('currency'))

			if  invoice_search.invoice_user_id.name != values.get('salesperson'):
				raise UserError(_('User(Salesperson) is different for "%s" .\n Please define same.') % values.get('salesperson'))

			if invoice_search.l10n_latam_document_type_id.code != str(values.get('td')):
				raise UserError(_('Type Document is different for "%s"-"%s" .\n Please define same.') % (invoice_search.l10n_latam_document_type_id.code,values.get('td')))

			if invoice_search.ref != str(values.get('nro_comprobante')):
				raise UserError(_('Invoice Number is different for "%s" .\n Please define same.') % values.get('nro_comprobante'))

			if invoice_search.glosa != values.get('glosa'):
				raise UserError(_('Glosa is different for "%s" .\n Please define same.') % values.get('glosa'))

			if invoice_search.state != 'draft':
				raise UserError(_('Invoice "%s" is not in Draft state.') % invoice_search.name)

			self.make_invoice_line(values, invoice_search)
			return invoice_search
						
		else:
			if str(values.get('customer')) == '':
				raise UserError(_('Please assign a Partner.'))
			else:
				s = str(values.get("customer"))
				vat = s.rstrip('0').rstrip('.') if '.' in s else s
				partner_id = self.find_partner(vat)
			currency_id = self.find_currency(values.get('currency'))
			salesperson_id = self.find_sales_person(values.get('salesperson'))
			if values.get('date_invoice') == '':
				raise UserError(_('Please assign a date'))
			else:
				inv_date = self.find_invoice_date(values.get('date_invoice'))
				inv_date_due = self.find_invoice_date(values.get('date_invoice_due'))

			if str(values.get('td')) == '':
				raise UserError(_('Please assign a Type Document.'))
			else:
				l10n_latam_document_type_id = self.find_type_document(str(values.get('td')))
			doc_relac_type_document_id = None
			if str(values.get('td_doc_relac')) != '':
				doc_relac_type_document_id = self.find_type_document(str(values.get('td_doc_relac')))

			if str(values.get('nro_comprobante')) == '':
				raise UserError(_('Please assign a Invoice Number.'))

			if str(values.get('glosa')) == '':
				raise UserError(_('Please assign a Glosa.'))

			value_inv_arr = {
				'name': values.get('invoice') if self.sequence_opt == 'custom' else '/',
				'partner_id' : partner_id.id,
				'currency_id' : currency_id.id,
				'invoice_user_id':salesperson_id.id,
				'custom_seq': True if self.sequence_opt == 'custom' else False,
				'system_seq': True if self.sequence_opt == 'system' else False,
				'move_type' : self.type_import,
				'date':inv_date,
				'invoice_date':inv_date,
				'invoice_date_due': inv_date_due,
				'journal_id' : self.journal_id.id,
				'invoice_name' : values.get('invoice'),
				'l10n_latam_document_type_id' : l10n_latam_document_type_id.id,
				'ref' : str(values.get('nro_comprobante')),
				'glosa': str(values.get('glosa')),
				'company_id' : self.company_id.id,
				'type_op_det': values.get('tipo_ope'),
				'date_detraccion': values.get('fecha_detrac'),
				'voucher_number': values.get('nro_comp_detrac'),
				'detra_amount': values.get('monto_detrac'),
				'detraction_percent_id': self.env['detractions.catalog.percent'].search([('code','=',values.get('bien_servi'))],limit=1).id if values.get('bien_servi') != '' else None
			}
			
			if inv_date != inv_date_due:
				value_inv_arr['invoice_payment_term_id'] = None
			if values.get('tc') != '':
				value_inv_arr['currency_rate'] = float(values.get('tc'))
			inv_id = invoice_obj.create(value_inv_arr)
			if values.get('tc') == '':
				inv_id._get_currency_rate()
			inv_id._onchange_tc_per()
			self.make_invoice_line(values, inv_id)
			if doc_relac_type_document_id:
				inv_id.write({'doc_invoice_relac' :([(0,0,{
				'type_document_id' : doc_relac_type_document_id.id if doc_relac_type_document_id else None,
				'date' : values.get('fecha_doc_relac'),
				'nro_comprobante' :values.get('nro_doc_relac'),
				'amount_currency':values.get('monto_me_doc_relac'),
				'amount' : values.get('total_mn_doc_relac'),
				'bas_amount' : values.get('base_doc_relac'),
				'tax_amount' : values.get('igv_doc_relac')
			})]) })
			inv_id.write({'name': values.get('invoice') if self.sequence_opt == 'custom' else '/'})
			return inv_id
	
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

	def find_analytic_account(self, code):
		analytic_obj = self.env['account.analytic.account']
		analytic_search = analytic_obj.search([('code', '=', str(code)),('company_id','=',self.company_id.id)],limit=1)
		if analytic_search:
			return analytic_search
		else:
			raise UserError(_('No existe una Cuenta Analitica con el Codigo "%s" en esta Compañia') % code)

	def find_currency(self, name):
		currency_obj = self.env['res.currency']
		currency_search = currency_obj.search([('name', '=', name)],limit=1)
		if currency_search:
			return currency_search
		else:
			raise UserError(_(' "%s" Currency are not available.') % name)

	def find_sales_person(self, name):
		sals_person_obj = self.env['res.users']
		partner_search = sals_person_obj.search([('name', '=', name)],limit=1)
		if partner_search:
			return partner_search
		else:
			raise UserError(_('Not Valid Salesperson Name "%s"') % name)
	
	def find_work_order(self, name):
		work_order_id = self.env['project.project'].search([
      		('name', '=', name)
        ],limit=1)
		if not work_order_id:
			raise UserError(f'No se encontro la Orden de Trabajo "{name}".')
		return work_order_id
		
			

	def find_partner(self, name):
		partner_obj = self.env['res.partner']
		partner_search = partner_obj.search([('vat', '=', str(name)),('parent_id','=',False)],limit=1)
		if partner_search:
			return partner_search
		else:
			raise UserError(_('No existe un Partner con el Nro de Documento "%s"') % name)

	def find_type_document(self,name):
		type_document_search = self.env['l10n_latam.document.type'].search([('code','=',name)],limit=1)
		if type_document_search:
			return type_document_search
		else:
			raise UserError(_('No existe un Tipo de Comprobante con el Codigo"%s"') % name)
	
	def find_invoice_date(self, date):
		DATETIME_FORMAT = "%Y-%m-%d"
		i_date = datetime.strptime(date, DATETIME_FORMAT).date()
		return i_date

	#NUEVA FUNCIONALIDAD
	def get_excel_not_partner(self,partner):			
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']

		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		namefile = 'partners_missing.xlsx'
		
		workbook = Workbook(direccion + namefile)
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		worksheet = workbook.add_worksheet("PARTNER")

		worksheet.set_tab_color('blue')

		HEADERS = [u'NRO PARTNER']

		worksheet = ReportBase.get_headers(worksheet,HEADERS,0,0,formats['boldbord'])
		x=1
  
		for line in partner:
			worksheet.write(x,0,line if line else '',formats['especial1'])
			x += 1

		widths = [15]

		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()

		f = open(direccion + namefile, 'rb')
		return self.env['popup.it'].get_file(u'Partner no encontrados.xlsx',base64.encodebytes(b''.join(f.readlines())))

	
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
	
	def action_cancel(self):
		for move in self.move_ids:
			move.button_cancel()
			move.line_ids.unlink()
			move.name = "/"
			move.unlink()

		self.state = 'cancel'

	def action_draft(self):
		self.state = 'draft'

	def download_auto(self):
		if not self.type_import:
			raise UserError('Falta escoger Tipo')
		if not self.account_opt:
			raise UserError('Falta escoger "Cuenta de" en pestaña Cuenta')
		
		return {
			 'type' : 'ir.actions.act_url',
			 'url': '/web/binary/download_document?model=import.invoice.it&id=%s'%(self.id),
			 'target': 'new',
			 }