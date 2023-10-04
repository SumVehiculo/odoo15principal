# -*- coding: utf-8 -*-

from mimetypes import init
from string import digits
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
import base64
from PIL import Image

class AccountSurrenderRequestsIt(models.Model):
	_name = 'account.surrender.requests.it'
	_inherit = ['mail.thread']

	name = fields.Char(string='Motivo')
	date = fields.Date(string='Fecha Entrega')
	employee_id = fields.Many2one('res.partner',string='Empleado')
	journal_id = fields.Many2one('account.journal',string='Moneda')
	user_id = fields.Many2one('res.users',string='Aprobado por')
	statement_id = fields.Many2one('account.bank.statement',string='Entrega')
	amount= fields.Float(string='Monto',digits=(12,2),default=0)
	einvoice_catalog_payment_id = fields.Many2one('einvoice.catalog.payment',string='Medio de Pago', copy=False)
	state = fields.Selection([('draft', 'Solicitado'), ('done', 'Aprobado'), ('cancel', 'Cancelado')],string='Estado', default='draft')
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)

	invoice_ids = fields.One2many('account.surrender.requests.invoice.line','request_id',string='Detalle')
	move_ids = fields.One2many('account.move','surrender_request_id',string='Facturas')
	count_moves = fields.Integer(compute='compute_count_moves')
	amount_use = fields.Float(string='Monto Rendido',compute='compute_amount_use',store=True)
	amount_render = fields.Float(string='Saldo',compute='compute_amount_render',store=True)

	dest_location = fields.Char(string='Lugar de Destino')
	date_from = fields.Date('Start Date', states={'done': [('readonly', True)]})
	date_to = fields.Date('End Date', states={'done': [('readonly', True)]})

	def action_autocomplete_partner(self):
		for reg in self:
			for line in reg.invoice_ids:
				line.onchange_vat()

	@api.depends('invoice_ids','journal_id','state')
	def compute_amount_use(self):
		for request in self:
			amount=0
			for line in request.invoice_ids:
				if line.currency_id.id != (request.journal_id.currency_id.id or request.company_id.currency_id.id):
					amount += line.currency_id._convert(line.price, (request.journal_id.currency_id or request.company_id.currency_id), request.company_id, line.invoice_date)
				else:
					amount += line.price
			request.amount_use = amount

	@api.depends('amount','amount_use')
	def compute_amount_render(self):
		for request in self:
			request.amount_render = request.amount - request.amount_use

	@api.depends('move_ids')
	def compute_count_moves(self):
		for i in self:
			i.count_moves = len(i.move_ids)

	@api.model_create_multi
	def create(self, vals_list):
		rslt = super(AccountSurrenderRequestsIt, self).create(vals_list)
		users = self.env['res.groups'].search([('name','=','Aprobar Solicitudes de Rendicion')],limit=1).users
		for sur in rslt:
			self.env['mail.mail'].sudo().create({
							'subject': 'Rendicion %s' % (sur.name),
							'body_html':'Estimado (a),<br/>'
										u'Se informa que se creó la Solicitud de Rendicion Nro %s en el sistema <br/>' % (sur.name),
							'email_to': '%s'%(','.join(i.login for i in users))}).send()
		return rslt

	def action_done(self):
		if self.statement_id:
			raise UserError(u'Ya tiene una entrega asignada.')
		if not self.date:
			raise UserError(u'Falta asignar Fecha Entrega')
		if not self.employee_id:
			raise UserError(u'Falta asignar Empleado')
		if not self.name:
			raise UserError(u'Falta asignar Motivo')
		if not self.journal_id:
			raise UserError(u'Falta asignar Diario')
		statement_id = self.env['account.bank.statement'].create({
			'journal_id': self.journal_id.id,
			'date': self.date,
			'company_id':self.company_id.id,
			'date_surrender':self.date,
			'employee_id':self.employee_id.id,
			'memory':self.name,
			'amount_surrender':self.amount,
			'einvoice_catalog_payment_id':self.einvoice_catalog_payment_id.id,
		})
		self.user_id = self.env.uid
		self.state = 'done'
		
		self.statement_id = statement_id.id

		self.env['mail.mail'].sudo().create({
						'subject': 'Rendicion %s' % (statement_id.name),
						'body_html':'Estimado (a) %s,<br/>'
									u'Se informa que se le aprobó su solicitud de entrega rendir por un monto de %s,  puede hacer seguimiento de la fecha de deposito ingresando a la entrega a rendir nro : %s <br/>' % (self.employee_id.name, str(self.amount) +' '+ (self.journal_id.currency_id.name if self.journal_id.currency_id else 'PEN'),statement_id.name),
						'email_to': self.employee_id.email}).send()
	
	def action_cancel(self):
		if self.statement_id:
			raise UserError(u'No puede cancelar una solicitud si tiene asignada una entrega, primero tiene que eliminarla.')
		if len(self.move_ids)>0:
			raise UserError(u'No puede cancelar esta operación, primero tiene que eliminar las Facturas creadas')
		self.state = 'cancel'
	
	def action_draft(self):
		self.state = 'draft'
	
	def create_line_request(self):
		if self.statement_id.state != 'open':
			raise UserError(u'No puede agregar/eliminar datos a Rendición si no se encuentra en estado "Nuevo"')
		self.statement_id.line_ids.unlink()
		for line in self.invoice_ids:
			if line.currency_id.id != (self.journal_id.currency_id.id or self.company_id.currency_id.id):
				amount =line.currency_id._convert(line.price, (self.journal_id.currency_id or self.company_id.currency_id), self.company_id, line.invoice_date) *-1
			else:
				amount = line.price*-1

			self.statement_id.write({'line_ids': [(0,0,{
			'date': line.invoice_date,
			'name': line.name,
			'payment_ref': line.name,
			'ref': line.nro_comp,
			'type_document_id': line.render_type_document_id.type_document_id.id,
			'partner_id': line.partner_id.id if line.partner_id else None,
			'amount': amount,
			'company_id': self.company_id.id,
			})]})
		self.statement_id.create_journal_entry_surrender()
		return self.env['popup.it'].get_message('Se agregaron correctamente los registros.')
	
	def create_invoices(self):
		m = self.env['render.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1)

		if not m.invoice_journal_id.id:
			raise UserError(u"No esta configurado el Diario de Facturas en Parametros Principales de Rendiciones para su Compañía")
		invoice_obj = self.env['account.move']
		for inv in self.invoice_ids:
			if not inv.invoice_id and inv.create_invoice_line:
				invoice = invoice_obj.search([
					('move_type', '=', 'in_invoice'),
					('partner_id','=',inv.partner_id.id),
					('l10n_latam_document_type_id','=',inv.render_type_document_id.type_document_id.id),
					('ref','=',inv.nro_comp),
					('company_id','=',self.company_id.id)
				],limit=1)
				
				if not invoice:
					value_inv_arr = {
					'partner_id' : inv.partner_id.id,
					'currency_id' : inv.currency_id.id,
					'invoice_user_id':self.env.uid,
					'move_type' : 'in_invoice',
					'date':inv.date,
					'invoice_date':inv.invoice_date,
					'invoice_date_due': inv.invoice_date_due,
					'journal_id' : m.invoice_journal_id.id,
					'l10n_latam_document_type_id' : inv.render_type_document_id.type_document_id.id,
					'ref' : inv.nro_comp,
					'glosa': inv.name,
					'company_id' : self.company_id.id,
					}
					if inv.invoice_date != inv.invoice_date_due:
						value_inv_arr['invoice_payment_term_id'] = None
					invoice = invoice_obj.create(value_inv_arr)
					invoice._get_currency_rate()
				else:
					raise UserError('El comprobante "%s"-"%s"-"%s ya existe en el sistema."'%(inv.partner_id.name,inv.render_type_document_id.type_document_id.code, inv.nro_comp))

				###Add invoice line
				if inv.product_id.property_account_expense_id:
					account = inv.product_id.property_account_expense_id
				elif inv.product_id.categ_id.property_account_expense_categ_id:
					account = inv.product_id.categ_id.property_account_expense_categ_id
				else:
					account_search = self.env['ir.property'].search([('name', '=', 'property_account_expense_categ_id'),('company_id','=',self.company_id.id)],limit=1)
					account = account_search.value_reference
					account = account.split(",")[1]
					account = self.env['account.account'].browse(account)
				
				if not inv.account_id:
					raise UserError(u'La cuenta es obligatoria.')
				
				vals = {
					'product_id' : inv.product_id.id,
					'quantity' : 1,
					'price_unit' : inv.price,
					'name' : inv.name,
					'account_id' : inv.account_id.id,
					'analytic_account_id': inv.analytic_id.id if inv.analytic_id else None,
					'product_uom_id' : inv.product_id.uom_po_id.id,
					'company_id' : self.company_id.id,
					'l10n_latam_document_type_id': inv.render_type_document_id.type_document_id.id
				}
				if inv.tax_id:
					vals.update({'tax_ids':([(6,0,[inv.tax_id.id])])})

				invoice.write({'invoice_line_ids' :([(0,0,vals)]), 'surrender_request_id':self.id })
				invoice._get_currency_rate()
				invoice._compute_amount()
				invoice.flush()
				if inv.date != inv.invoice_date:
					invoice.write({'date': inv.date})
				invoice.action_post()
				inv.invoice_id = invoice.id
		
		return self.env['popup.it'].get_message('Se crearon correctamente las Facturas.')
	
	def open_entries(self):
		self.ensure_one()
		action = self.env.ref('account.action_move_journal_line').read()[0]
		domain = [('id', 'in', self.move_ids.ids)]
		context = dict(self.env.context, default_invoice_id=self.id)
		views = [(self.env.ref('account.view_move_tree').id, 'tree'), (False, 'form'), (False, 'kanban')]
		return dict(action, domain=domain, context=context, views=views)

	def get_report(self):
		import io
		from xlsxwriter.workbook import Workbook

		ReportBase = self.env['report.base']
		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'SolcitudRend.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		worksheet = workbook.add_worksheet("Detalles")
		worksheet.set_tab_color('blue')
		currency = self.journal_id.currency_id or self.company_id.currency_id
		if self.company_id.logo:
			img = io.BytesIO(base64.b64decode(self.company_id.logo))
			imgs = Image.open(img)

			cell_width = 260
			cell_height = 60

			x_scale = cell_width/imgs.width
			y_scale = cell_height/imgs.height
			
			worksheet.insert_image('A1', "logo.png",{'image_data':img,'x_scale': x_scale, 'y_scale': y_scale})

		formats['numberdos'].set_num_format('"%s" #,##0.00' % currency.symbol)
		formats['numberdos'].set_font_name('Arial')
		formats['especial1'].set_font_name('Arial')
		formats['dateformat'].set_font_name('Arial')

		especial5 = workbook.add_format({'bold': True})
		especial5.set_align('center')
		especial5.set_font_size(18)

		especial3 = workbook.add_format({'bold': True,'font_color':'#17375E'})
		especial3.set_font_size(11)

		boldbord = workbook.add_format({'bold': True})
		boldbord.set_border(style=1)
		boldbord.set_align('center')
		boldbord.set_align('vcenter')
		boldbord.set_font_size(11)
		boldbord.set_bg_color('#BFBFBF')


		worksheet.merge_range(1,0,1,7, u'Liquidación de Viajes y Representación', especial5)

		worksheet.write(4,0, "Lugar de Destino: %s"%(self.dest_location or ''), especial3)
		worksheet.write(5,0, "Motivo de Viaje: %s"%(self.name), especial3)
		worksheet.write(6,0, "Periodo: Del %s al %s"%(str(self.date_from),str(self.date_to)), especial3)

		worksheet.write(4,5, "Trabajador: %s"%(self.employee_id.name or ''), especial3)
		worksheet.write(5,5, "DNI: %s"%(self.employee_id.vat or ''), especial3)
		worksheet.write(6,5, "Moneda: %s"%(currency.currency_unit_label), especial3)
		

		HEADERS = [u'N°',u'Razon Social',u'RUC',u'Fecha','Tipo','Numero',u'Descripción',u'Total']
		worksheet = ReportBase.get_headers(worksheet,HEADERS,8,0,boldbord)

		x=9
		tot = 0

		for c, line in enumerate(self.invoice_ids):
			worksheet.write(x,0,str(c+1),formats['especial1'])
			worksheet.write(x,1,line.partner_id.name if line.partner_id else '',formats['especial1'])
			worksheet.write(x,2,line.partner_id.vat if line.partner_id else '',formats['especial1'])
			worksheet.write(x,3,line.invoice_date if line.invoice_date else '',formats['dateformat'])
			worksheet.write(x,4,line.render_type_document_id.code if line.render_type_document_id else '',formats['especial1'])
			worksheet.write(x,5,line.nro_comp if line.nro_comp else '',formats['especial1'])
			worksheet.write(x,6,line.name if line.name else '',formats['especial1'])
			worksheet.write_number(x,7,(line.currency_id._convert(line.price, (self.journal_id.currency_id or self.company_id.currency_id), self.company_id, line.invoice_date)) if line.price else 0,formats['numberdos'])
			tot += (line.currency_id._convert(line.price, (self.journal_id.currency_id or self.company_id.currency_id), self.company_id, line.invoice_date)) if line.price else 0
			x += 1
		x+=1
		worksheet.write(x,6, 'TOTALES', formats['especial1'])
		worksheet.write(x,7, tot, formats['numberdos'])
		x+=2
		worksheet.write(x,6, 'MONTO ENTREGADO', formats['especial1'])
		worksheet.write(x,7, self.amount, formats['numberdos'])
		x+=2
		worksheet.write(x,6, 'MONTO A REEMBOLSAR', formats['especial1'])
		worksheet.write(x,7, self.amount_render, formats['numberdos'])
		x+=5

		especial2 = workbook.add_format({'bold': True})
		especial2.set_align('center')
		especial2.set_align('vcenter')
		especial2.set_text_wrap()
		especial2.set_font_size(11)
		especial2.set_top()

		worksheet.write(x,1, 'Trabajador', especial2)
		worksheet.write(x,6, 'Gerente General', especial2)
		
		widths = [2,35,17,13,6,13,50,14]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()

		f = open(direccion +'SolcitudRend.xlsx', 'rb')

		return self.env['popup.it'].get_file('Solicitud de Entrega.xlsx',base64.encodebytes(b''.join(f.readlines())))

class AccountSurrenderRequestsInvoiceLine(models.Model):
	_name = 'account.surrender.requests.invoice.line'

	request_id = fields.Many2one('account.surrender.requests.it',string='Main')
	vat = fields.Char(string=u'Doc. Proveedor ')
	partner_id = fields.Many2one('res.partner',string='Proveedor', readonly=True)
	currency_id = fields.Many2one('res.currency',string='Moneda')
	product_id = fields.Many2one('product.product',string='Producto')
	name = fields.Char(string=u'Descripción')
	price = fields.Float(string='Monto',digits=(64,2))
	tax_id = fields.Many2one('account.tax',string='Impuesto')
	date = fields.Date(string='Fecha Contable')
	invoice_date = fields.Date(string=u'Fecha Emisión')
	invoice_date_due = fields.Date(string=u'Fecha Vencimiento')
	render_type_document_id = fields.Many2one('render.type.document',string='Tipo de Documento')
	nro_comp = fields.Char(string='Nro Comprobante')
	analytic_id = fields.Many2one('account.analytic.account',string=u'Cuenta Analítica')
	invoice_id = fields.Many2one('account.move',string='Factura')
	account_id = fields.Many2one('account.account',string='Cuenta',readonly=True)
	create_invoice_line = fields.Boolean(string='Crea Factura',default=True)

	@api.onchange('vat')
	def onchange_vat(self):
		for line in self:
			if line.vat:
				line.partner_id = self.env['res.partner'].search([('vat','=',line.vat)],limit=1).id

	@api.onchange('invoice_date')
	def onchange_invoice_date(self):
		for line in self:
			line.date = line.invoice_date
			line.invoice_date_due = line.invoice_date

	@api.onchange('product_id')
	def onchange_product_id(self):
		for line in self:
			if line.product_id:
				line.name = line._get_computed_name()
				line.account_id = line.compute_account()
				line.tax_id = line.product_id.supplier_taxes_id[0].id if line.product_id.supplier_taxes_id else None

	def _get_computed_name(self):
		self.ensure_one()

		if not self.product_id:
			return ''

		if self.partner_id.lang:
			product = self.product_id.with_context(lang=self.partner_id.lang)
		else:
			product = self.product_id

		values = []
		if product.partner_ref:
			values.append(product.partner_ref)
		if product.description_purchase:
			values.append(product.description_purchase)
		return '\n'.join(values)
	
	@api.depends('product_id')
	def compute_account(self):
		self.ensure_one()
		if self.product_id.property_account_expense_id:
			account = self.product_id.property_account_expense_id
		elif self.product_id.categ_id.property_account_expense_categ_id:
			account = self.product_id.categ_id.property_account_expense_categ_id
		else:
			account_search = self.env['ir.property'].search([('name', '=', 'property_account_expense_categ_id'),('company_id','=',self.env.company.id)],limit=1)
			account = account_search.value_reference
			account = account.split(",")[1]
			account = self.env['account.account'].browse(account)
		
		return account.id
	
	@api.onchange('nro_comp','render_type_document_id')
	def _get_ref(self):
		for i in self:
			digits_serie = ('').join(i.render_type_document_id.type_document_id.digits_serie*['0'])
			digits_number = ('').join(i.render_type_document_id.type_document_id.digits_number*['0'])
			if i.nro_comp:
				if '-' in i.nro_comp:
					partition = i.nro_comp.split('-')
					if len(partition) == 2:
						serie = digits_serie[:-len(partition[0])] + partition[0]
						number = digits_number[:-len(partition[1])] + partition[1]
						i.nro_comp = serie + '-' + number