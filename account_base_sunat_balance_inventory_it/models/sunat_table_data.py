# -*- coding: utf-8 -*-

from odoo import models, fields, api

class SunatTableData(models.Model):
	_name = 'sunat.table.data'
	_description = 'Sunat Table Data'	

	@api.depends('fiscal_year_id')
	def _get_name(self):
		for i in self:
			i.name = i.fiscal_year_id.name

	name = fields.Char(compute=_get_name,store=True)
	fiscal_year_id = fields.Many2one('account.fiscal.year',string=u'Ejercicio',required=True)
	sunat = fields.Selection([('030100','030100'),('031800','031800'),('031900','031900'),('032000','032000'),('032400','032400'),('032500','032500')],string='Codigo Sunat')
	line_ids = fields.One2many('sunat.table.data.line','main_id',string='Detalle',copy=True)
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)


class SunatTableDataLine(models.Model):
	_name = 'sunat.table.data.line'
	_description = 'Sunat Table Data Line'	

	main_id = fields.Many2one('sunat.table.data',string=u'Main',ondelete="cascade")
	code = fields.Char(string=u'Código')
	name = fields.Char(string=u'Descripción')
	amount = fields.Float(string=u'Monto',digits=(64,2))
	capital = fields.Float(string=u'Capital',digits=(64,2))
	acc_inv = fields.Float(string=u'Acciones de Inversión',digits=(64,2))
	cap_add = fields.Float(string=u'Capital Adicional',digits=(64,2))
	res_no_real = fields.Float(string=u'Resultados no Realizados',digits=(64,2))
	reserv_leg = fields.Float(string=u'Reservas Legales',digits=(64,2))
	o_reverv = fields.Float(string=u'Otras Reservas',digits=(64,2))
	res_acum = fields.Float(string=u'Resultados Acumulados',digits=(64,2))
	dif_conv = fields.Float(string=u'Diferencias de Conversión',digits=(64,2))
	ajus_patr = fields.Float(string=u'Ajustes al Patrimonio',digits=(64,2))
	res_neto_ej = fields.Float(string=u'Resultado Neto del Ejercicio',digits=(64,2))
	exc_rev = fields.Float(string=u'Excedente de Revaluación',digits=(64,2))
	res_ejerc = fields.Float(string=u'Resultado del Ejercicio',digits=(64,2))

class SunatTableData031601(models.Model):
	_name = 'sunat.table.data.031601'
	_description = 'Sunat Table Data 031601'	

	@api.depends('fiscal_year_id')
	def _get_name(self):
		for i in self:
			i.name = i.fiscal_year_id.name

	name = fields.Char(compute=_get_name,store=True)
	fiscal_year_id = fields.Many2one('account.fiscal.year',string=u'Ejercicio',required=True)
	importe_cap = fields.Float(string=u'Importe Capital',digits=(64,2))
	valor_nominal = fields.Float(string=u'Valor Nominal',digits=(64,2))
	nro_acc_sus = fields.Float(string=u'Número de Acciones Suscritas',digits=(64,2))
	nro_acc_pag = fields.Float(string=u'Número de Acciones Pagadas',digits=(64,2))
	estado = fields.Selection([('1',u'La operación corresponde al periodo.'),
								('8',u'La operación corresponde a un periodo anterior y NO ha sido anotada en dicho periodo.'),
								('9',u'La operación corresponde a un periodo anterior y SI ha sido anotada en dicho periodo.')],string='Estado PLE',default='1')
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	
	_sql_constraints = [
		('sunat_table_031601_fiscal_year_id', 'UNIQUE (fiscal_year_id,company_id)', u'Ya existe un registro con el mismo Año Fiscal en esta Compañía!')
	]

class SunatTableData031602(models.Model):
	_name = 'sunat.table.data.031602'
	_description = 'Sunat Table Data 031602'	

	@api.depends('fiscal_year_id')
	def _get_name(self):
		for i in self:
			i.name = i.fiscal_year_id.name

	name = fields.Char(compute=_get_name,store=True)
	fiscal_year_id = fields.Many2one('account.fiscal.year',string=u'Ejercicio',required=True)
	partner_id = fields.Many2one('res.partner',string=u'Socio',required=True)
	tipo = fields.Selection([('01',u'ACCIONES CON DERECHO A VOTO'),
								('02',u'ACCIONES SIN DERECHO A VOTO'),
								('03',u'PARTICIPACIONES'),
								('04',u'OTROS')],string='Tipo',default='01')
	num_acciones = fields.Integer(string=u'Número de Acciones')
	percentage = fields.Float(string=u'Porcentaje de Participación')
	estado = fields.Selection([('1',u'La operación corresponde al periodo.'),
								('8',u'La operación corresponde a un periodo anterior y NO ha sido anotada en dicho periodo.'),
								('9',u'La operación corresponde a un periodo anterior y SI ha sido anotada en dicho periodo.')],string='Estado PLE',default='1')
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	
	_sql_constraints = [
		('sunat_table_031602_fiscal_year_id', 'UNIQUE (fiscal_year_id,company_id,partner_id)', u'Ya existe un registro con el mismo Año Fiscal y Socio en esta Compañía!')
	]

class SunatTableData031700(models.Model):
	_name = 'sunat.table.data.031700'
	_description = 'Sunat Table Data 031700'

	@api.depends('fiscal_year_id')
	def _get_name(self):
		for i in self:
			i.name = i.fiscal_year_id.name

	name = fields.Char(compute=_get_name,store=True)
	fiscal_year_id = fields.Many2one('account.fiscal.year',string=u'Ejercicio',required=True)
	line_ids = fields.One2many('sunat.table.data.031700.line','main_id',string='Detalles')
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)

	_sql_constraints = [
		('sunat_table_031700_fiscal_year_id', 'UNIQUE (fiscal_year_id,company_id)', u'Ya existe un registro con el mismo Año Fiscal en esta Compañía!')
	]

	def get_data(self):
		self.env.cr.execute("""DELETE FROM sunat_table_data_031700_line WHERE main_id = %d"""%(self.id))
		self.env.cr.execute("""SELECT aa.id as account_id, F2.* FROM get_f2_register('%s',%d,'pen') F2
							LEFT JOIN account_account aa ON aa.code = F2.cuenta AND aa.company_id = %d
							WHERE aa.clasification_sheet in ('0','1')"""%(self.fiscal_year_id.name + '12',self.company_id.id,self.company_id.id))
		obj_line = self.env['sunat.table.data.031700.line']
		data = self.env.cr.dictfetchall()
		for line in data:
			obj_line.create({
				'main_id': self.id,
				'account_id': line['account_id'],
				'si_debe': line['debe_inicial'],
				'si_haber': line['haber_inicial'],
				'debe': line['debe'],
				'haber': line['haber'],
				'suma_debe': line['debe_inicial'] + line['debe'],
				'suma_haber': line['haber_inicial'] + line['haber'],
				'deudor': line['saldo_deudor'],
				'acreedor': line['saldo_acreedor'],
				'estado': '1'
			})
		

class SunatTableData031700Line(models.Model):
	_name = 'sunat.table.data.031700.line'
	_description = 'Sunat Table Data 031700 Line'

	main_id = fields.Many2one('sunat.table.data.031700',string=u'Main',ondelete="cascade")
	account_id = fields.Many2one('account.account',string='Cuenta',readonly=True)
	si_debe = fields.Float(string='SI Debe',digits=(12,2),readonly=True)
	si_haber = fields.Float(string='SI Haber',digits=(12,2),readonly=True)
	debe = fields.Float(string='Debe',digits=(12,2),readonly=True)
	haber = fields.Float(string='Haber',digits=(12,2),readonly=True)
	suma_debe = fields.Float(string='Suma Debe',digits=(12,2),readonly=True)
	suma_haber = fields.Float(string='Suma Haber',digits=(12,2),readonly=True)
	deudor = fields.Float(string='Deudor',digits=(12,2),readonly=True)
	acreedor = fields.Float(string='Acreedor',digits=(12,2),readonly=True)
	t_debe = fields.Float(string='T Debe',digits=(12,2))
	t_haber = fields.Float(string='T Haber',digits=(12,2))
	n_deudor = fields.Float(string='N Deudor',digits=(12,2),compute='compute_n_deudor',store=True)
	n_acreedor = fields.Float(string='N Acreedor',digits=(12,2),compute='compute_n_acreedor',store=True)
	activo = fields.Float(string='Activo',digits=(12,2),compute='compute_activo',store=True)
	pasivo = fields.Float(string='Pasivo',digits=(12,2),compute='compute_pasivo',store=True)
	perdidas = fields.Float(string='Perdidas',digits=(12,2),compute='compute_perdidas',store=True)
	ganancias = fields.Float(string='Ganancias',digits=(12,2),compute='compute_ganancias',store=True)
	adiciones = fields.Float(string='Adiciones',digits=(12,2))
	deducciones = fields.Float(string='Deducciones',digits=(12,2))
	estado = fields.Selection([('1',u'La operación corresponde al periodo.'),
								('8',u'La operación corresponde a un periodo anterior y NO ha sido anotada en dicho periodo.'),
								('9',u'La operación corresponde a un periodo anterior y SI ha sido anotada en dicho periodo.')],string='Estado PLE',default='1')

	@api.depends('deudor','t_debe')
	def compute_n_deudor(self):
		for i in self:
			i.n_deudor = i.deudor + i.t_debe

	@api.depends('acreedor','t_haber')
	def compute_n_acreedor(self):
		for i in self:
			i.n_acreedor = i.acreedor + i.t_haber

	@api.depends('account_id.clasification_sheet','n_deudor')
	def compute_activo(self):
		for i in self:
			i.activo = i.n_deudor if i.account_id.clasification_sheet == '0' else 0

	@api.depends('account_id.clasification_sheet','n_acreedor')
	def compute_pasivo(self):
		for i in self:
			i.pasivo = i.n_acreedor if i.account_id.clasification_sheet == '0' else 0

	@api.depends('account_id.clasification_sheet','n_deudor')
	def compute_perdidas(self):
		for i in self:
			i.perdidas = i.n_deudor if i.account_id.clasification_sheet == '1' else 0

	@api.depends('account_id.clasification_sheet','n_acreedor')
	def compute_ganancias(self):
		for i in self:
			i.ganancias = i.n_acreedor if i.account_id.clasification_sheet == '1' else 0