# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import calendar
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare, float_is_zero
import base64

class AccountAssetCategory(models.Model):
	_name = 'account.asset.category'
	_description = 'Asset category'

	active = fields.Boolean(default=True)
	name = fields.Char(required=True, index=True, string="Categoria de Activo")
	account_analytic_id = fields.Many2one('account.analytic.account', string='Cuenta Analitica')
	analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Etiqueta Analitca')
	account_asset_id = fields.Many2one('account.account', string='Cuenta de Activo', required=True, domain=[('internal_type','=','other'), ('deprecated', '=', False)], help="Account used to record the purchase of the asset at its original price.")
	account_depreciation_id = fields.Many2one('account.account', string='Cuenta de Depreciacion', required=True, domain=[('internal_type','=','other'), ('deprecated', '=', False)], help="Account used in the depreciation entries, to decrease the asset value.")
	account_depreciation_expense_id = fields.Many2one('account.account', string='Cuenta de Gasto Depreciacion', required=True, domain=[('internal_type','=','other'), ('deprecated', '=', False)], help="Account used in the periodical entries, to record a part of the asset as expense.")
	account_retire_id = fields.Many2one('account.account', string='Cuenta de Retiro', domain=[('internal_type','=','other'), ('deprecated', '=', False)])
	journal_id = fields.Many2one('account.journal', string='Diario', required=True)
	company_id = fields.Many2one('res.company', string=u'Compañia', required=True, default=lambda self: self.env['res.company']._company_default_get('account.asset.category'))
	method = fields.Selection([('linear', 'Linear'), ('degressive', 'Degressive')], string='Metodo de Calculo', required=True, default='linear')
	method_number = fields.Integer(string='Numero de Entradas', default=5, help="The number of depreciations needed to depreciate your asset")
	method_period = fields.Integer(string='Una Entrada Cada', default=1, help="State here the time between 2 depreciations, in months", required=True)
	method_progress_factor = fields.Float('Degressive Factor', default=0.3)
	method_time = fields.Selection([('number', 'Numero de Entradas'), ('end', 'Ultimo Dia')], string='Tiempo Basado En', required=True, default='number')
	method_end = fields.Date('Ending date')
	prorata = fields.Boolean(string='Prorata Temporis', help='Indicates that the first depreciation entry for this asset have to be done from the purchase date instead of the first of January')
	open_asset = fields.Boolean(string='Auto-Confirmar Activos', help="Check this if you want to automatically confirm the assets of this category when created by invoices.")
	group_entries = fields.Boolean(string='Agrupar Entradas de Diario', help="Check this if you want to group the generated entries by categories.")
	type = fields.Selection([('sale', 'Sale: Revenue Recognition'), ('purchase', 'Purchase: Asset')], required=True, index=True, default='purchase')
	date_first_depreciation = fields.Selection([
		('last_day_period', 'Primer Dia del Mes Siguiente'),
		('manual', 'Manual')],
		string=u'Inicio de Depreciacion', default='manual', required=True)
	depreciation_rate = fields.Float(string=u'Tasa de Depreciación')

	@api.onchange('account_asset_id')
	def onchange_account_asset(self):
		if self.type == "purchase":
			self.account_depreciation_id = self.account_asset_id
		elif self.type == "sale":
			self.account_depreciation_expense_id = self.account_asset_id

	@api.onchange('depreciation_rate')
	def onchange_depreciation_rate(self):
		if self.depreciation_rate and self.depreciation_rate != 0:
			self.method_number = (100/(self.depreciation_rate))*12

	@api.onchange('type')
	def onchange_type(self):
		if self.type == 'sale':
			self.prorata = True
			self.method_period = 1
		else:
			self.method_period = 1

	@api.onchange('method_time')
	def _onchange_method_time(self):
		if self.method_time != 'number':
			self.prorata = False


class AccountAssetAsset(models.Model):
	_name = 'account.asset.asset'
	_description = 'Asset/Revenue Recognition'
	_inherit = ['mail.thread']

	entry_count = fields.Integer(compute='_entry_count', string='# Asset Entries')
	name = fields.Char(string='Activo', required=True, readonly=True, states={'draft': [('readonly', False)]})
	code = fields.Char(string='Codigo', size=32, readonly=True, states={'draft': [('readonly', False)]})
	value = fields.Float(string='Valor de Compra', required=True, readonly=True, digits=0, states={'draft': [('readonly', False)]})
	currency_id = fields.Many2one('res.currency', string='Moneda', required=True, readonly=True, states={'draft': [('readonly', False)]},
		default=lambda self: self.env.user.company_id.currency_id.id)
	company_id = fields.Many2one('res.company', string=u'Compañía', required=True, readonly=True, states={'draft': [('readonly', False)]},
		default=lambda self: self.env['res.company']._company_default_get('account.asset.asset'))
	note = fields.Text()
	category_id = fields.Many2one('account.asset.category', string='Categoria  de Activo', required=True, change_default=True, readonly=True, states={'draft': [('readonly', False)]})
	parent_id = fields.Many2one('account.asset.asset', string='Padre del activo', change_default=True, readonly=True, states={'draft': [('readonly', False)]})
	date = fields.Date(string='Fecha de Compra', required=True, default=fields.Date.context_today)
	state = fields.Selection([('draft', 'Borrador'), ('open', 'Ejecutando'), ('unsubscribe', 'De Baja'), ('close', 'Cerrado')], 'Estado', required=True, copy=False, default='draft')
	active = fields.Boolean(default=True)
	partner_id = fields.Many2one('res.partner', string='Proveedor', readonly=True, states={'draft': [('readonly', False)]})
	method = fields.Selection([('linear', 'Linear'), ('degressive', 'Degressive')], string='Metodo de Calcula', required=True, readonly=True, states={'draft': [('readonly', False)]}, default='linear')
	method_number = fields.Integer(string='Numero de Depreciaciones', readonly=True, states={'draft': [('readonly', False)]}, default=5, help="The number of depreciations needed to depreciate your asset")
	method_period = fields.Integer(string='Numero de Meses en Cada Periodo', required=True, readonly=True, default=12, states={'draft': [('readonly', False)]})
	method_end = fields.Date(string='Ending Date', readonly=True, states={'draft': [('readonly', False)]})
	method_progress_factor = fields.Float(string='Degressive Factor', readonly=True, default=0.3, states={'draft': [('readonly', False)]})
	value_residual = fields.Float(compute='_amount_residual', method=True, digits=0, string='Valor Residual')
	method_time = fields.Selection([('number', 'Number of Entries'), ('end', 'Ending Date')], string='Time Method', required=True, readonly=True, default='number', states={'draft': [('readonly', False)]},
		help="Choose the method to use to compute the dates and number of entries.\n"
			 "  * Number of Entries: Fix the number of entries and the time between 2 depreciations.\n"
			 "  * Ending Date: Choose the time between 2 depreciations and the date the depreciations won't go beyond.")
	prorata = fields.Boolean(string='Prorata Temporis', readonly=True, states={'draft': [('readonly', False)]},
		help='Indicates that the first depreciation entry for this asset have to be done from the asset date (purchase date) instead of the first January / Start date of fiscal year',default=False)
	depreciation_line_ids = fields.One2many('account.asset.depreciation.line', 'asset_id', string='Depreciation Lines', readonly=True, states={'draft': [('readonly', False)], 'open': [('readonly', False)]})
	depreciation_line_me_ids = fields.One2many('account.asset.depreciation.line', 'asset_id', string='Depreciation Lines ME', readonly=True, states={'draft': [('readonly', False)], 'open': [('readonly', False)]})
	salvage_value = fields.Float(string=u'Valor de Recuperación', digits=0, readonly=True, states={'draft': [('readonly', False)]},
		help="It is the amount you plan to have that you cannot depreciate.")
	invoice_id = fields.Many2one('account.move', string='Factura', states={'draft': [('readonly', False)]}, copy=False)
	type = fields.Selection(related="category_id.type", string='Type', required=True)
	tipo = fields.Selection([('adquisicion', 'Adquisiciones'), ('mejoras', 'Mejoras'),('otros','Otros Ajustes')], default='adquisicion')
	account_analytic_id = fields.Many2one('account.analytic.account', string=u'Cuenta Analítica')
	analytic_tag_ids = fields.Many2many('account.analytic.tag', string=u'Etiqueta Analítica')
	valor_retiro = fields.Float(string='Valor de Retiro',digits=(64,2))
	depreciacion_retiro = fields.Float(string='Depreciacion del Retiro',digits=(64,2))
	referencia = fields.Char(string='Referencia', readonly=True, states={'draft': [('readonly', False)]},size=32)
	autorizacion_depreciacion = fields.Char(string=u'Autorización para la Depreciación',size=100)
	nro_comprobante = fields.Char(string='Nro Comprobante')
	f_baja = fields.Date(string='Fecha de Baja')
	move_baja_id = fields.Many2one('account.move', string='Asiento de Baja', copy=False)
	ean13 = fields.Char(string=u'Código EAN13')
	cuo = fields.Char(string=u'CUO',help='Para PLE de Inventario y Balances, si tiene completo el campo Factura no es necesario')
	code_asiento = fields.Char(string=u'Asiento Contable',help='Para PLE de Inventario y Balances, si tiene completo el campo Factura no es necesario')

	date_first_depreciation = fields.Selection([
		('last_day_period', 'Primer dia del mes siguiente'),
		('manual', 'Manual')],
		string=u'Inicio de Depreciación', default='manual',
		readonly=True, states={'draft': [('readonly', False)]}, required=True)
	first_depreciation_manual_date = fields.Date(
		string=u'Fecha Inicio de Depreciación',
		help='Note that this date does not alter the computation of the first journal entry in case of prorata temporis assets. It simply changes its accounting date'
	)

	#PARAMETERS IT
	location = fields.Char(string=u'Ubicación')
	brand = fields.Char(string=u'Marca')
	model = fields.Char(string=u'Modelo')
	plaque = fields.Char(string=u'Serie y/o Placa')
	contract_date = fields.Date(string='Fecha de Contrato')
	contract_number = fields.Char(string=u'Nro. Contrato Arrendamiento Financiero',size=50)
	date_start_contract = fields.Date(string=u'Fecha de Inicio del Contrato Arrendamiento')
	fees_number = fields.Integer(string=u'Nro. Cuotas Pactadas')
	amount_total_contract = fields.Float(string=u'Monto Total Contrato De Arrendamiento',digits=(12,2))
	only_format_74 = fields.Boolean(string='Mostrar solo en Formato 7.4',default=False)
	years_depreciations = fields.Integer(string=u'Años de Depreciación')
	depreciation_rate = fields.Float(string=u'Tasa de Depreciación')
	depreciation_authorization = fields.Char(string=u'Autorización de Depreciación',size=50)

	##CAMPOS EN DOLARES
	tipo_cambio_d = fields.Float(string='Tipo de Cambio Dolares',digits=(12,3),default=1)
	bruto_dolares = fields.Float(string='Valor Compra ME',digits=(64,2))
	salvage_value_me = fields.Float(string=u'Valor de Recuperación ME',compute='compute_salvage_value_me',digits=(64,2))
	value_residual_me = fields.Float(compute='_amount_residual_me',string=u'Valor Residual ME',digits=(64,2))

	#PLE
	table_13_ple = fields.Selection([('1','1 NACIONES UNIDAS'),('3',u'3 GS1 (EAN-UCC)'),('9','9 OTROS')],string='Tabla 13')
	table_18_ple = fields.Selection([('1','1 NO REVALUADO O REVALUADO SIN EFECTO TRIBUTARIO'),('2',u'2 REVALUADO CON EFECTO TRIBUTARIO')],string='Tabla 18')
	table_19_ple = fields.Selection([('1','1 ACTIVOS EN DESUSO'),('2',u'2 ACTIVOS OBSOLETOS'),('9',u'9 RESTO DE ACTIVOS')],string='Tabla 19')
	table_20_ple = fields.Selection([('1','1 LINEA RECTA'),('2',u'2 UNIDADES PRODUCIDAS'),('9',u'9 OTROS')],string='Tabla 20')
	campo37_ple = fields.Selection([('1',u'1 La operación corresponde al periodo.'),
	('8',u'8 La operación corresponde a un periodo anterior y NO ha sido anotada en dicho periodo.'),
	('9',u'9 La operación corresponde a un periodo anterior y SI ha sido anotada en dicho periodo.')],string=u'Estado de la operación',default='1')
	periodo_ple = fields.Many2one('account.period',string='Periodo')

	@api.depends('tipo_cambio_d','salvage_value')
	def compute_salvage_value_me(self):
		for asset in self:
			asset.salvage_value_me = asset.salvage_value/asset.tipo_cambio_d if asset.tipo_cambio_d != 0 else asset.salvage_value

	@api.onchange('date')
	def change_date_tc(self):
		for asset in self:
			if not asset.tipo_cambio_d or asset.tipo_cambio_d in (0,1):
				tc = self.env['res.currency.rate'].search([('name','=',asset.date),('company_id','=',asset.company_id.id)],limit=1).sale_type
				asset.tipo_cambio_d = tc if tc else 1
			if not asset.bruto_dolares or asset.bruto_dolares == asset.value:
				asset.bruto_dolares = asset.value/asset.tipo_cambio_d

	@api.onchange('method_number','method_period')
	def change_method_number(self):
		years_dep = 0
		if self.method_number and self.method_period:
			years_dep = (self.method_number*self.method_period)/12
			self.years_depreciations = years_dep

	@api.onchange('years_depreciations')
	def change_years_depreciations(self):
		dep_rate = 0
		if self.years_depreciations:
			dep_rate = 100/(self.years_depreciations)
			self.depreciation_rate = dep_rate

	def unlink(self):
		for asset in self:
			if asset.state in ['open', 'close']:
				raise UserError(_('You cannot delete a document that is in %s state.') % (asset.state,))
			for depreciation_line in asset.depreciation_line_ids:
				if depreciation_line.move_id:
					raise UserError(_('You cannot delete a document that contains posted entries.'))
		return super(AccountAssetAsset, self).unlink()

	@api.model
	def _cron_generate_entries(self):
		first_day_of_month = date.today().replace(day=1)
		last_day_of_month = date.today().replace(day=calendar.monthrange(date.today().year,date.today().month)[1])
		self.compute_generated_entries(first_day_of_month,last_day_of_month)
	
	def get_asset_report(self):
		import io
		from xlsxwriter.workbook import Workbook

		ReportBase = self.env['report.base']
		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'Asset_rep.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		worksheet = workbook.add_worksheet("ACTIVO PEN")
		worksheet.set_tab_color('blue')

		formats['numberdosespecial'].set_num_format('"%s" #,##0.00' % self.currency_id.symbol)

		worksheet.merge_range(1,0,1,5, self.name, formats['especial4'])

		worksheet.write(3,0, u"Código:", formats['especial2'])
		worksheet.write(4,0, "Nombre:", formats['especial2'])
		worksheet.write(5,0, "Padre:", formats['especial2'])
		worksheet.write(6,0, "Fecha Compra:", formats['especial2'])
		worksheet.write(7,0, "Fecha Inicio:", formats['especial2'])
		worksheet.write(8,0, u"Cuenta Analítica:", formats['especial2'])
		worksheet.write(9,0, u"Etiqueta Analítica:", formats['especial2'])
		worksheet.write(3,2, u"Moneda:", formats['especial2'])
		worksheet.write(4,2, u"Compañía:", formats['especial2'])
		worksheet.write(5,2, u"Valor Compra:", formats['especial2'])
		worksheet.write(6,2, u"Valor Recuperación:", formats['especial2'])
		worksheet.write(7,2, u"Valor Residual:", formats['especial2'])
		worksheet.write(8,2, u"Proveedor:", formats['especial2'])
		worksheet.write(9,2, u"Factura:", formats['especial2'])

		worksheet.write(3,1, self.code if self.code else '', formats['especial4'])
		worksheet.write(4,1, self.name if self.name else '', formats['especial4'])
		worksheet.write(5,1, self.parent_id.name if self.parent_id else '', formats['especial4'])
		worksheet.write(6,1, self.date, formats['especialdate'])
		worksheet.write(7,1, self.first_depreciation_manual_date if self.first_depreciation_manual_date else '', formats['especialdate'])
		worksheet.write(8,1, self.account_analytic_id.name if self.account_analytic_id else '', formats['especial4'])
		worksheet.write(9,1, ','.join("'%s'"%str(i.name) for i in self.analytic_tag_ids) if self.analytic_tag_ids else '', formats['especial4'])
		worksheet.write(3,3, self.currency_id.name if self.currency_id else '', formats['especial4'])
		worksheet.write(4,3, self.company_id.name if self.company_id else '', formats['especial4'])
		worksheet.write_number(5,3, self.value , formats['numberdosespecial'])
		worksheet.write_number(6,3, self.salvage_value , formats['numberdosespecial'])
		worksheet.write_number(7,3, self.value_residual , formats['numberdosespecial'])
		worksheet.write(8,1, self.partner_id.name if self.partner_id else '', formats['especial4'])
		worksheet.write(9,1, self.invoice_id.display_name if self.invoice_id else '', formats['especial4'])

		HEADERS = ['FECHA',u'DEPRECIACIÓN',u'DEPRECIACIÓN ACUM.','RESIDUAL']
		worksheet = ReportBase.get_headers(worksheet,HEADERS,11,0,formats['boldbord'])

		x=12

		for line in self.depreciation_line_ids:
			worksheet.write(x,0,line.depreciation_date if line.depreciation_date else '',formats['dateformat'])
			worksheet.write(x,1,line.amount if line.amount else 0,formats['numberdos'])
			worksheet.write(x,2,line.depreciated_value if line.depreciated_value else 0,formats['numberdos'])
			worksheet.write(x,3,line.remaining_value if line.remaining_value else 0,formats['numberdos'])
			x += 1

		widths = [20,30,20,40]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		####################################################
		worksheet = workbook.add_worksheet("ACTIVO USD")
		worksheet.set_tab_color('blue')

		worksheet.merge_range(1,0,1,5, self.name, formats['especial4'])

		worksheet.write(3,0, u"Código:", formats['especial2'])
		worksheet.write(4,0, "Nombre:", formats['especial2'])
		worksheet.write(5,0, "Padre:", formats['especial2'])
		worksheet.write(6,0, "Fecha Compra:", formats['especial2'])
		worksheet.write(7,0, "Fecha Inicio:", formats['especial2'])
		worksheet.write(8,0, u"Cuenta Analítica:", formats['especial2'])
		worksheet.write(9,0, u"Etiqueta Analítica:", formats['especial2'])
		worksheet.write(3,2, u"Moneda:", formats['especial2'])
		worksheet.write(4,2, u"Compañía:", formats['especial2'])
		worksheet.write(5,2, u"Valor Compra:", formats['especial2'])
		worksheet.write(6,2, u"Valor Recuperación:", formats['especial2'])
		worksheet.write(7,2, u"Valor Residual:", formats['especial2'])
		worksheet.write(8,2, u"Proveedor:", formats['especial2'])
		worksheet.write(9,2, u"Factura:", formats['especial2'])

		worksheet.write(3,1, self.code if self.code else '', formats['especial4'])
		worksheet.write(4,1, self.name if self.name else '', formats['especial4'])
		worksheet.write(5,1, self.parent_id.name if self.parent_id else '', formats['especial4'])
		worksheet.write(6,1, self.date, formats['especialdate'])
		worksheet.write(7,1, self.first_depreciation_manual_date if self.first_depreciation_manual_date else '', formats['especialdate'])
		worksheet.write(8,1, self.account_analytic_id.name if self.account_analytic_id else '', formats['especial4'])
		worksheet.write(9,1, ','.join("'%s'"%str(i.name) for i in self.analytic_tag_ids) if self.analytic_tag_ids else '', formats['especial4'])
		worksheet.write(3,3, self.currency_id.name if self.currency_id else '', formats['especial4'])
		worksheet.write(4,3, self.company_id.name if self.company_id else '', formats['especial4'])
		worksheet.write_number(5,3, self.bruto_dolares , formats['numberdosespecial'])
		worksheet.write_number(6,3, self.salvage_value_me , formats['numberdosespecial'])
		worksheet.write_number(7,3, self.value_residual_me , formats['numberdosespecial'])
		worksheet.write(8,1, self.partner_id.name if self.partner_id else '', formats['especial4'])
		worksheet.write(9,1, self.invoice_id.display_name if self.invoice_id else '', formats['especial4'])

		worksheet = ReportBase.get_headers(worksheet,HEADERS,11,0,formats['boldbord'])

		x=12

		for line in self.depreciation_line_me_ids:
			worksheet.write(x,0,line.depreciation_date if line.depreciation_date else '',formats['dateformat'])
			worksheet.write(x,1,line.amount_me if line.amount_me else 0,formats['numberdos'])
			worksheet.write(x,2,line.depreciated_value_me if line.depreciated_value_me else 0,formats['numberdos'])
			worksheet.write(x,3,line.remaining_value_me if line.remaining_value_me else 0,formats['numberdos'])
			x += 1

		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()

		f = open(direccion +'Asset_rep.xlsx', 'rb')

		return self.env['popup.it'].get_file('%s.xlsx'%(self.name),base64.encodebytes(b''.join(f.readlines())))

	def change_to_unsubscribe(self):
		if not self.value:
			raise UserError(u'No esta establecido el Valor de Compra del Activo.')
		if not self.f_baja:
			raise UserError(u'No esta establecida la Fecha de Baja del Activo.')
		if not self.category_id.account_retire_id:
			raise UserError(u'No esta establecida la Cuenta de Retiro en la Categoría del Activo.')

		f_baja_end = self.f_baja - timedelta(days=self.f_baja.day)
		f_baja_start = f_baja_end.replace(day=1)
		line_baja = self.env['account.asset.depreciation.line'].search([
			('asset_id', '=', self.id), ('depreciation_date', '>=', f_baja_start), ('depreciation_date', '<=', f_baja_end)],limit=1)
		
		##### MOVE ID BAJA #######
		
		lineas = []
		vals = (0,0,{
				'account_id': self.category_id.account_asset_id.id,
				'name': 'BAJA DE ACTIVO '+self.name,
				'debit': 0,
				'credit': self.value,
				'company_id': self.company_id.id,
			})
		lineas.append(vals)

		vals = (0,0,{
				'account_id': self.category_id.account_depreciation_id.id,
				'name': 'BAJA DE ACTIVO '+self.name,
				'debit': line_baja.depreciated_value,
				'credit': 0,
				'company_id': self.company_id.id,
			})
		lineas.append(vals)

		vals = (0,0,{
				'account_id': self.category_id.account_retire_id.id,
				'name': 'BAJA DE ACTIVO '+self.name,
				'debit': self.value - line_baja.depreciated_value,
				'credit': 0,
				'company_id': self.company_id.id,
			})
		lineas.append(vals)

		move_id = self.env['account.move'].create({
			'company_id': self.company_id.id,
			'journal_id': self.category_id.journal_id.id,
			'date': self.f_baja,
			'line_ids':lineas,
			'ref': 'BAJA-'+ (self.code or ''),
			'glosa':'BAJA DE ACTIVO '+self.name,
			'move_type':'entry'})

		move_id.post()
		self.move_baja_id = move_id.id

		self.env['account.asset.depreciation.line'].search([('asset_id', '=', self.id), ('depreciation_date', '>', f_baja_end)]).unlink()
		self.state = 'unsubscribe'

		return self.env['popup.it'].get_message(u'SE DIÓ DE BAJA ESTE ACTIVO.')
		############################

	@api.model
	def compute_generated_entries(self, date_start, date_end, asset_type=None):
		# Entries generated : one by grouped category and one by asset from ungrouped category
		created_move_ids = []
		type_domain = []
		if asset_type:
			type_domain = [('type', '=', asset_type)]

		ungrouped_assets = self.env['account.asset.asset'].search(type_domain + [('state', '=', 'open'), ('category_id.group_entries', '=', False),'|',('f_baja','=',False),('f_baja','>',date_start)])
		created_move_ids += ungrouped_assets._compute_entries(date_start, date_end, group_entries=False)

		for grouped_category in self.env['account.asset.category'].search(type_domain + [('group_entries', '=', True)]):
			assets = self.env['account.asset.asset'].search([('state', '=', 'open'), ('category_id', '=', grouped_category.id),'|',('f_baja','=',False),('f_baja','>',date_start)])
			created_move_ids += assets._compute_entries(date_start, date_end, group_entries=True)
		return created_move_ids

	def _compute_board_amount(self, sequence, residual_amount, amount_to_depr, undone_dotation_number, posted_depreciation_line_ids, total_days, depreciation_date):
		amount = 0
		if sequence == undone_dotation_number:
			amount = residual_amount
		else:
			if self.method == 'linear':
				amount = amount_to_depr / (undone_dotation_number - len(posted_depreciation_line_ids))
				if self.prorata:
					amount = amount_to_depr / self.method_number
					if sequence == 1:
						date = self.date
						if self.method_period % 12 != 0:
							month_days = calendar.monthrange(date.year, date.month)[1]
							days = month_days - date.day + 1
							amount = (amount_to_depr / self.method_number) / month_days * days
						else:
							days = (self.company_id.compute_fiscalyear_dates(date)['date_to'] - date).days + 1
							amount = (amount_to_depr / self.method_number) / total_days * days
			elif self.method == 'degressive':
				amount = residual_amount * self.method_progress_factor
				if self.prorata:
					if sequence == 1:
						date = self.date
						if self.method_period % 12 != 0:
							month_days = calendar.monthrange(date.year, date.month)[1]
							days = month_days - date.day + 1
							amount = (residual_amount * self.method_progress_factor) / month_days * days
						else:
							days = (self.company_id.compute_fiscalyear_dates(date)['date_to'] - date).days + 1
							amount = (residual_amount * self.method_progress_factor) / total_days * days
		return amount

	def _compute_board_undone_dotation_nb(self, depreciation_date, total_days):
		undone_dotation_number = self.method_number
		if self.method_time == 'end':
			end_date = self.method_end
			undone_dotation_number = 0
			while depreciation_date <= end_date:
				depreciation_date = date(depreciation_date.year, depreciation_date.month, depreciation_date.day) + relativedelta(months=+self.method_period)
				undone_dotation_number += 1
		if self.prorata:
			undone_dotation_number += 1
		return undone_dotation_number

	def action_depreciation_board_me(self):
		for asset in self:
			self.env.cr.execute("""update account_asset_asset set bruto_dolares = value/tipo_cambio_d where id = %d;"""%(asset.id))
			self.env.cr.execute("""update account_asset_depreciation_line set amount_me = T.amount/T.tipo_cambio_d, remaining_value_me = T.remaining_value/T.tipo_cambio_d,
								depreciated_value_me = T.depreciated_value/T.tipo_cambio_d from
								(select l.id, l.amount, l.remaining_value, l.depreciated_value, a.tipo_cambio_d from account_asset_depreciation_line l
								left join account_asset_asset a on a.id = l.asset_id
								where a.id = %d)T
								where account_asset_depreciation_line.id = T.id"""%(asset.id))

	def compute_depreciation_board(self):
		self.ensure_one()
		self.change_date_tc()
		
		posted_depreciation_line_ids = self.depreciation_line_ids.filtered(lambda x: x.move_check).sorted(key=lambda l: l.depreciation_date)
		unposted_depreciation_line_ids = self.depreciation_line_ids.filtered(lambda x: not x.move_check)

		# Remove old unposted depreciation lines. We cannot use unlink() with One2many field
		commands = [(2, line_id.id, False) for line_id in unposted_depreciation_line_ids]

		if self.value_residual != 0.0:
			amount_to_depr = residual_amount = self.value_residual
			amount_to_depr_me = residual_amount_me = self.value_residual_me

			# if we already have some previous validated entries, starting date is last entry + method period
			if posted_depreciation_line_ids and posted_depreciation_line_ids[-1].depreciation_date:
				last_depreciation_date = fields.Date.from_string(posted_depreciation_line_ids[-1].depreciation_date)
				depreciation_date = last_depreciation_date + relativedelta(months=+self.method_period)
			else:
				# depreciation_date computed from the purchase date
				depreciation_date = self.date
				if self.date_first_depreciation == 'last_day_period':
					# depreciation_date = the last day of the month
					depreciation_date = depreciation_date + relativedelta(day=1) + relativedelta(months=1)
					# ... or fiscalyear depending the number of period
					if self.method_period == 12:
						depreciation_date = depreciation_date + relativedelta(month=int(self.company_id.fiscalyear_last_month))
						depreciation_date = depreciation_date + relativedelta(day=int(self.company_id.fiscalyear_last_day))
						if depreciation_date < self.date:
							depreciation_date = depreciation_date + relativedelta(years=1)
				elif self.first_depreciation_manual_date and self.first_depreciation_manual_date != self.date:
					# depreciation_date set manually from the 'first_depreciation_manual_date' field
					depreciation_date = self.first_depreciation_manual_date

			total_days = (depreciation_date.year % 4) and 365 or 366
			month_day = depreciation_date.day
			undone_dotation_number = self._compute_board_undone_dotation_nb(depreciation_date, total_days)
			usd = self.env.ref('base.USD')

			for x in range(len(posted_depreciation_line_ids), undone_dotation_number):
				sequence = x + 1
				amount = self._compute_board_amount(sequence, residual_amount, amount_to_depr, undone_dotation_number, posted_depreciation_line_ids, total_days, depreciation_date)
				amount_me = self._compute_board_amount(sequence, residual_amount_me, amount_to_depr_me, undone_dotation_number, posted_depreciation_line_ids, total_days, depreciation_date)
				amount = self.currency_id.round(amount)
				amount_me = usd.round(amount_me)
				if float_is_zero(amount, precision_rounding=self.currency_id.rounding):
					continue
				residual_amount -= amount
				residual_amount_me -= amount_me
				vals = {
					'amount': amount,
					'amount_me': amount_me,
					'asset_id': self.id,
					'sequence': sequence,
					'name': (self.code or '') + '/' + str(sequence),
					'remaining_value': residual_amount,
					'remaining_value_me': residual_amount_me,
					'depreciated_value': self.value - (self.salvage_value + residual_amount),
					'depreciated_value_me': self.bruto_dolares - (self.salvage_value_me + residual_amount_me),
					'depreciation_date': depreciation_date,
				}
				commands.append((0, False, vals))

				depreciation_date = depreciation_date + relativedelta(months=+self.method_period)

				if month_day > 28 and self.date_first_depreciation == 'manual':
					max_day_in_month = calendar.monthrange(depreciation_date.year, depreciation_date.month)[1]
					depreciation_date = depreciation_date.replace(day=min(max_day_in_month, month_day))

				# datetime doesn't take into account that the number of days is not the same for each month
				if not self.prorata and self.method_period % 12 != 0 and self.date_first_depreciation == 'last_day_period':
					max_day_in_month = calendar.monthrange(depreciation_date.year, depreciation_date.month)[1]
					depreciation_date = depreciation_date.replace(day=1)

		self.write({'depreciation_line_ids': commands})

		return True

	
	def validate(self):
		self.write({'state': 'open'})
		fields = [
			'method',
			'method_number',
			'method_period',
			'method_end',
			'method_progress_factor',
			'method_time',
			'salvage_value',
			'invoice_id',
		]
		ref_tracked_fields = self.env['account.asset.asset'].fields_get(fields)
		for asset in self:
			tracked_fields = ref_tracked_fields.copy()
			if asset.method == 'linear':
				del(tracked_fields['method_progress_factor'])
			if asset.method_time != 'end':
				del(tracked_fields['method_end'])
			else:
				del(tracked_fields['method_number'])
			dummy, tracking_value_ids = asset._mail_track(tracked_fields, dict.fromkeys(fields))
			asset.message_post(subject=_('Asset created'), tracking_value_ids=tracking_value_ids)

	def _return_disposal_view(self, move_ids):
		name = _('Disposal Move')
		view_mode = 'form'
		if len(move_ids) > 1:
			name = _('Disposal Moves')
			view_mode = 'tree,form'
		return {
			'name': name,
			'view_type': 'form',
			'view_mode': view_mode,
			'res_model': 'account.move',
			'type': 'ir.actions.act_window',
			'target': 'current',
			'res_id': move_ids[0],
		}

	def _get_disposal_moves(self):
		move_ids = []
		for asset in self:
			unposted_depreciation_line_ids = asset.depreciation_line_ids.filtered(lambda x: not x.move_check)
			if unposted_depreciation_line_ids:
				old_values = {
					'method_end': asset.method_end,
					'method_number': asset.method_number,
				}

				# Remove all unposted depr. lines
				commands = [(2, line_id.id, False) for line_id in unposted_depreciation_line_ids]

				# Create a new depr. line with the residual amount and post it
				sequence = len(asset.depreciation_line_ids) - len(unposted_depreciation_line_ids) + 1
				today = fields.Datetime.today()
				vals = {
					'amount': asset.value_residual,
					'asset_id': asset.id,
					'sequence': sequence,
					'name': (asset.code or '') + '/' + str(sequence),
					'remaining_value': 0,
					'depreciated_value': asset.value - asset.salvage_value,  # the asset is completely depreciated
					'depreciation_date': today,
				}
				commands.append((0, False, vals))
				asset.write({'depreciation_line_ids': commands, 'method_end': today, 'method_number': sequence})
				tracked_fields = self.env['account.asset.asset'].fields_get(['method_number', 'method_end'])
				changes, tracking_value_ids = asset._message_track(tracked_fields, old_values)
				if changes:
					asset.message_post(subject=_('Asset sold or disposed. Accounting entry awaiting for validation.'), tracking_value_ids=tracking_value_ids)
				move_ids += asset.depreciation_line_ids[-1].create_move(post_move=False)

		return move_ids

	
	def set_to_close(self):
		move_ids = self._get_disposal_moves()
		if move_ids:
			return self._return_disposal_view(move_ids)
		# Fallback, as if we just clicked on the smartbutton
		return self.open_entries()

	def set_to_draft(self):
		self.write({'state': 'draft'})

	@api.depends('value', 'salvage_value', 'depreciation_line_ids.move_check', 'depreciation_line_ids.amount')
	def _amount_residual(self):
		for rec in self:
			total_amount = 0.0
			for line in rec.depreciation_line_ids:
				if line.move_check:
					total_amount += line.amount
			rec.value_residual = rec.value - total_amount - rec.salvage_value
	
	@api.depends('bruto_dolares', 'salvage_value_me', 'depreciation_line_ids.move_check', 'depreciation_line_ids.amount_me')
	def _amount_residual_me(self):
		for rec in self:
			total_amount_me = 0.0
			for line in rec.depreciation_line_ids:
				if line.move_check:
					total_amount_me += line.amount_me
			rec.value_residual_me = rec.bruto_dolares - total_amount_me - rec.salvage_value_me

	@api.onchange('company_id')
	def onchange_company_id(self):
		self.currency_id = self.company_id.currency_id.id

	
	@api.onchange('date','date_first_depreciation')
	def onchange_date_first_depreciation(self):
		if self.date_first_depreciation == 'manual':
			self.first_depreciation_manual_date = self.date

		if self.date_first_depreciation == 'last_day_period':
			date_first = self.date
			self.first_depreciation_manual_date = date_first.replace(day=1) + relativedelta(months=1)
			

	@api.depends('depreciation_line_ids.move_id')
	def _entry_count(self):
		for asset in self:
			res = self.env['account.asset.depreciation.line'].search_count([('asset_id', '=', asset.id), ('move_id', '!=', False)])
			asset.entry_count = res or 0


	@api.constrains('prorata', 'method_time')
	def _check_prorata(self):
		if self.prorata and self.method_time != 'number':
			raise ValidationError(_('Prorata temporis can be applied only for the "number of depreciations" time method.'))

	@api.onchange('category_id')
	def onchange_category_id(self):
		vals = self.onchange_category_id_values(self.category_id.id)
		# We cannot use 'write' on an object that doesn't exist yet
		if vals:
			for k, v in vals['value'].items():
				setattr(self, k, v)

	def onchange_category_id_values(self, category_id):
		if category_id:
			category = self.env['account.asset.category'].browse(category_id)
			return {
				'value': {
					'method': category.method,
					'method_number': category.method_number,
					'method_time': category.method_time,
					'method_period': category.method_period,
					'method_progress_factor': category.method_progress_factor,
					'method_end': category.method_end,
					'prorata': category.prorata,
					'date_first_depreciation': category.date_first_depreciation,
					'account_analytic_id': category.account_analytic_id.id,
					'analytic_tag_ids': [(6, 0, category.analytic_tag_ids.ids)],
				}
			}

	@api.onchange('method_time')
	def onchange_method_time(self):
		if self.method_time != 'number':
			self.prorata = False

	
	def copy_data(self, default=None):
		if default is None:
			default = {}
		default['name'] = self.name + _(' (copy)')
		return super(AccountAssetAsset, self).copy_data(default)

	
	def _compute_entries(self, date_start, date_end, group_entries=False):
		depreciation_ids = self.env['account.asset.depreciation.line'].search([
			('asset_id', 'in', self.ids), ('depreciation_date', '>=', date_start), ('depreciation_date', '<=', date_end),
			('move_check', '=', False)])
		if group_entries:
			depreciation_ids = self.env['account.asset.depreciation.line'].search([
			('asset_id', 'in', self.ids), ('depreciation_date', '>=', date_start), ('depreciation_date', '<=', date_end),
			('move_check', '=', False)])
			return depreciation_ids.create_grouped_move(date_end)
		return depreciation_ids.create_move(date_end)

	@api.model
	def create(self, vals):
		asset = super(AccountAssetAsset, self.with_context(mail_create_nolog=True)).create(vals)
		asset.sudo().compute_depreciation_board()
		return asset
	
	def write(self, vals):
		res = super(AccountAssetAsset, self).write(vals)
		if 'depreciation_line_ids' not in vals and 'state' not in vals:
			if 'category_id' in vals or 'date_first_depreciation' in vals or 'method_period' in vals or 'first_depreciation_manual_date' in vals or 'method_number' in vals or 'method_period' in vals or 'depreciation_rate' in vals:
				for rec in self:
					rec.compute_depreciation_board()
		return res

	def open_entries(self):
		move_ids = []
		for asset in self:
			for depreciation_line in asset.depreciation_line_ids:
				if depreciation_line.move_id:
					move_ids.append(depreciation_line.move_id.id)
		return {
			'name': _('Journal Entries'),
			'view_type': 'form',
			'view_mode': 'tree,form',
			'res_model': 'account.move',
			'view_id': False,
			'type': 'ir.actions.act_window',
			'domain': [('id', 'in', move_ids)],
		}


class AccountAssetDepreciationLine(models.Model):
	_name = 'account.asset.depreciation.line'
	_description = 'Asset depreciation line'

	name = fields.Char(string='Depreciation Name', required=True, index=True)
	sequence = fields.Integer(required=True)
	asset_id = fields.Many2one('account.asset.asset', string='Asset', required=True, ondelete='cascade')
	parent_state = fields.Selection(related='asset_id.state', string='State of Asset')
	amount = fields.Float(string=u'Depreciación', digits=0, required=True)
	amount_me = fields.Float(string=u'Depreciación ME')
	remaining_value = fields.Float(string='Residual', digits=0, required=True)
	remaining_value_me = fields.Float(string='Residual ME', digits=0)
	depreciated_value = fields.Float(string=u'Depreciación Acumulada', required=True)
	depreciated_value_me = fields.Float(string=u'Depreciación Acumulada ME')
	depreciation_date = fields.Date(string=u'Fecha de Depreciación', index=True)
	move_id = fields.Many2one('account.move', string='Depreciation Entry')
	move_check = fields.Boolean(compute='_get_move_check', string='Linked', track_visibility='always', store=True)
	move_posted_check = fields.Boolean(compute='_get_move_posted_check', string='Posted', track_visibility='always', store=True)

	
	@api.depends('move_id')
	def _get_move_check(self):
		for line in self:
			line.move_check = bool(line.move_id)

	
	@api.depends('move_id.state')
	def _get_move_posted_check(self):
		for line in self:
			line.move_posted_check = True if line.move_id and line.move_id.state == 'posted' else False

	
	def create_move(self, date_end, post_move=True):
		created_moves = self.env['account.move']
		for line in self:
			if line.move_id:
				raise UserError(_(u'Esta depreciación ya está vinculada a un asiento de diario. Por favor publícalo o bórralo.'))
			move_vals = self._prepare_move(line,date_end)
			move = self.env['account.move'].create(move_vals)
			#line.write({'move_id': move.id, 'move_check': True})
			created_moves |= move

		if post_move and created_moves:
			created_moves.filtered(lambda m: any(m.asset_depreciation_ids.mapped('asset_id.category_id.open_asset'))).post()
		return [x.id for x in created_moves]

	def _prepare_move(self, line, date_end):
		category_id = line.asset_id.category_id
		account_analytic_id = line.asset_id.account_analytic_id
		analytic_tag_ids = line.asset_id.analytic_tag_ids
		depreciation_date = self.env.context.get('depreciation_date') or line.depreciation_date or fields.Date.context_today(self)
		company_currency = line.asset_id.company_id.currency_id
		current_currency = line.asset_id.currency_id
		prec = company_currency.decimal_places
		amount = current_currency._convert(
			line.amount, company_currency, line.asset_id.company_id, depreciation_date)
		asset_name = line.asset_id.name + ' (%s/%s)' % (line.sequence, len(line.asset_id.depreciation_line_ids))
		move_line_1 = {
			'name': asset_name,
			'account_id': category_id.account_depreciation_id.id,
			'debit': 0.0 if float_compare(amount, 0.0, precision_digits=prec) > 0 else -amount,
			'credit': amount if float_compare(amount, 0.0, precision_digits=prec) > 0 else 0.0,
			'partner_id': line.asset_id.partner_id.id,
			'analytic_account_id': account_analytic_id.id if category_id.type == 'sale' else False,
			'analytic_tag_ids': [(6, 0, category_id.analytic_tag_ids.ids)] if category_id.type == 'sale' else False,
			'currency_id': company_currency != current_currency and current_currency.id or False,
			'amount_currency': company_currency != current_currency and - 1.0 * line.amount or 0.0,
		}
		move_line_2 = {
			'name': asset_name,
			'account_id': category_id.account_depreciation_expense_id.id,
			'credit': 0.0 if float_compare(amount, 0.0, precision_digits=prec) > 0 else -amount,
			'debit': amount if float_compare(amount, 0.0, precision_digits=prec) > 0 else 0.0,
			'partner_id': line.asset_id.partner_id.id,
			'analytic_account_id': account_analytic_id.id if category_id.type == 'purchase' else False,
			'analytic_tag_ids': [(6, 0, category_id.analytic_tag_ids.ids)] if category_id.type == 'purchase' else False,
			'currency_id': company_currency != current_currency and current_currency.id or False,
			'amount_currency': company_currency != current_currency and line.amount or 0.0,
		}
		move_vals = {
			'ref': line.asset_id.code,
			'date': date_end,
			'journal_id': category_id.journal_id.id,
			'line_ids': [(0, 0, move_line_1), (0, 0, move_line_2)],
		}
		return move_vals

	def _prepare_move_grouped(self,date_end):
		asset_id = self[0].asset_id
		category_id = asset_id.category_id  # we can suppose that all lines have the same category
		account_analytic_id = asset_id.account_analytic_id
		analytic_tag_ids = asset_id.analytic_tag_ids
		#depreciation_date = self.env.context.get('depreciation_date') or fields.Date.context_today(self)
		amount = 0.0
		for line in self:
			# Sum amount of all depreciation lines
			company_currency = line.asset_id.company_id.currency_id
			current_currency = line.asset_id.currency_id
			company = line.asset_id.company_id
			amount += current_currency._convert(line.amount, company_currency, company, fields.Date.today())

		name = category_id.name + _(' (grouped)')
		move_line_1 = {
			'name': name,
			'account_id': category_id.account_depreciation_id.id,
			'debit': 0.0,
			'credit': amount,
			'journal_id': category_id.journal_id.id,
			'analytic_account_id': account_analytic_id.id if category_id.type == 'sale' else False,
			'analytic_tag_ids': [(6, 0, category_id.analytic_tag_ids.ids)] if category_id.type == 'sale' else False,
		}
		move_line_2 = {
			'name': name,
			'account_id': category_id.account_depreciation_expense_id.id,
			'credit': 0.0,
			'debit': amount,
			'journal_id': category_id.journal_id.id,
			'analytic_account_id': account_analytic_id.id if category_id.type == 'purchase' else False,
			'analytic_tag_ids': [(6, 0, category_id.analytic_tag_ids.ids)] if category_id.type == 'purchase' else False,
		}
		move_vals = {
			'ref': category_id.name,
			'date': date_end,
			'journal_id': category_id.journal_id.id,
			'line_ids': [(0, 0, move_line_1), (0, 0, move_line_2)],
		}

		return move_vals

	
	def create_grouped_move(self, date_end,post_move=True):
		if not self.exists():
			return []

		created_moves = self.env['account.move']
		move = self.env['account.move'].create(self._prepare_move_grouped(date_end))
		#self.write({'move_id': move.id, 'move_check': True})
		created_moves |= move

		if post_move and created_moves:
			self.post_lines_and_close_asset()
			created_moves.post()
		return [x.id for x in created_moves]

	
	def post_lines_and_close_asset(self):
		# we re-evaluate the assets to determine whether we can close them
		for line in self:
			line.log_message_when_posted()
			asset = line.asset_id
			if asset.currency_id.is_zero(asset.value_residual):
				asset.message_post(body=_("Document closed."))
				asset.write({'state': 'close'})

	
	def log_message_when_posted(self):
		def _format_message(message_description, tracked_values):
			message = ''
			if message_description:
				message = '<span>%s</span>' % message_description
			for name, values in tracked_values.items():
				message += '<div> &nbsp; &nbsp; &bull; <b>%s</b>: ' % name
				message += '%s</div>' % values
			return message

		for line in self:
			if line.move_id and line.move_id.state == 'draft':
				partner_name = line.asset_id.partner_id.name
				currency_name = line.asset_id.currency_id.name
				msg_values = {_('Currency'): currency_name, _('Amount'): line.amount}
				if partner_name:
					msg_values[_('Partner')] = partner_name
				msg = _format_message(_('Depreciation line posted.'), msg_values)
				line.asset_id.message_post(body=msg)

	
	def unlink(self):
		for record in self:
			if record.move_check:
				if record.asset_id.category_id.type == 'purchase':
					msg = _("You cannot delete posted depreciation lines.")
				else:
					msg = _("You cannot delete posted installment lines.")
				raise UserError(msg)
		return super(AccountAssetDepreciationLine, self).unlink()
