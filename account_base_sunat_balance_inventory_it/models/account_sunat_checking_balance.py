# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountSunatCheckingBalance(models.Model):
	_name = 'account.sunat.checking.balance'
	_description = 'Account Sunat Checking Balance'

	@api.depends('date')
	def _get_name(self):
		for i in self:
			i.name = str(i.date)

	name = fields.Char(compute=_get_name,store=True)
	date = fields.Date(string=u'Periodo',required=True)
	line_ids = fields.One2many('account.sunat.checking.balance.line','main_id',string='Detalles')
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)

	def get_data(self):
		self.env.cr.execute("""DELETE FROM account_sunat_checking_balance_line WHERE main_id = %d"""%(self.id))
		self.env.cr.execute("""SELECT aa.id as account_id, F2.* FROM get_f2_register_balance_inventory('%s','%s',%d) F2
							LEFT JOIN account_account aa ON aa.code = F2.cuenta AND aa.company_id = %d
							WHERE aa.clasification_sheet in ('0','1')"""%(self.date.strftime('%Y%m'),self.date.strftime('%Y/%m/%d'),self.company_id.id,self.company_id.id))
		obj_line = self.env['account.sunat.checking.balance.line']
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
				'state': '1'
			})
		

class AccountSunatCheckingBalanceLine(models.Model):
	_name = 'account.sunat.checking.balance.line'
	_description = 'Account Sunat Checking Balance Line'

	main_id = fields.Many2one('account.sunat.checking.balance',string=u'Main',ondelete="cascade")
	account_id = fields.Many2one('account.account',string='Cuenta',readonly=True)
	si_debe = fields.Float(string='SI Debe',digits=(12,2),readonly=True)
	si_haber = fields.Float(string='SI Haber',digits=(12,2),readonly=True)
	debe = fields.Float(string='Debe',digits=(12,2),readonly=True)
	haber = fields.Float(string='Haber',digits=(12,2),readonly=True)
	suma_debe = fields.Float(string='Suma Debe',digits=(12,2),readonly=True)
	suma_haber = fields.Float(string='Suma Haber',digits=(12,2),readonly=True)
	deudor = fields.Float(string='Deudor',digits=(12,2),readonly=True)
	acreedor = fields.Float(string='Acreedor',digits=(12,2),readonly=True)
	t_debe = fields.Float(string='T Debe',digits=(12,2),default=0)
	t_haber = fields.Float(string='T Haber',digits=(12,2),default=0)
	n_deudor = fields.Float(string='N Deudor',digits=(12,2),compute='compute_n_deudor',store=True)
	n_acreedor = fields.Float(string='N Acreedor',digits=(12,2),compute='compute_n_acreedor',store=True)
	activo = fields.Float(string='Activo',digits=(12,2),compute='compute_activo',store=True)
	pasivo = fields.Float(string='Pasivo',digits=(12,2),compute='compute_pasivo',store=True)
	perdidas = fields.Float(string='Perdidas',digits=(12,2),compute='compute_perdidas',store=True)
	ganancias = fields.Float(string='Ganancias',digits=(12,2),compute='compute_ganancias',store=True)
	adiciones = fields.Float(string='Adiciones',digits=(12,2),default=0)
	deducciones = fields.Float(string='Deducciones',digits=(12,2),default=0)
	state = fields.Selection([('1',u'La operación corresponde al periodo.'),
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