# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountSunatStatePatrimony(models.Model):
	_name = 'account.sunat.state.patrimony'
	_description = 'Account Sunat State Patrimony'	

	@api.depends('date','code')
	def _get_name(self):
		for i in self:
			i.name = str(i.date) + i.code

	name = fields.Char(compute=_get_name,store=True)
	date = fields.Date(string='Periodo',required=True)
	code = fields.Char(string=u'Código',size=6)
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
	state = fields.Selection([('1',u'La operación corresponde al periodo.'),
								('8',u'La operación corresponde a un periodo anterior y NO ha sido anotada en dicho periodo.'),
								('9',u'La operación corresponde a un periodo anterior y SI ha sido anotada en dicho periodo.')],string='Estado PLE',default='1')
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)