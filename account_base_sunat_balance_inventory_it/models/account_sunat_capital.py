# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountSunatCapital(models.Model):
	_name = 'account.sunat.capital'
	_description = 'Account Sunat Capital'	

	@api.depends('date')
	def _get_name(self):
		for i in self:
			i.name = str(i.date)

	name = fields.Char(compute=_get_name,store=True)
	date = fields.Date(string='Periodo',required=True)
	importe_cap = fields.Float(string=u'Importe Capital',digits=(64,2))
	valor_nominal = fields.Float(string=u'Valor Nominal',digits=(64,2))
	nro_acc_sus = fields.Float(string=u'Número de Acciones Suscritas',digits=(64,2))
	nro_acc_pag = fields.Float(string=u'Número de Acciones Pagadas',digits=(64,2))
	state = fields.Selection([('1',u'La operación corresponde al periodo.'),
								('8',u'La operación corresponde a un periodo anterior y NO ha sido anotada en dicho periodo.'),
								('9',u'La operación corresponde a un periodo anterior y SI ha sido anotada en dicho periodo.')],string='Estado PLE',default='1')
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)