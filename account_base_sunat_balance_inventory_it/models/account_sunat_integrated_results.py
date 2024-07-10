# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountSunatIntegratedResults(models.Model):
	_name = 'account.sunat.integrated.results'
	_description = 'Account SUNAT Integrated Results'

	@api.depends('date','code')
	def _get_name(self):
		for i in self:
			i.name = str(i.date) + i.code

	name = fields.Char(compute=_get_name,store=True)
	date = fields.Date(string='Periodo',required=True)
	code = fields.Char(string=u'Código',size=6)
	amount = fields.Float(string=u'Monto',digits=(64,2))
	state = fields.Selection([('1',u'La operación corresponde al periodo.'),
								('8',u'La operación corresponde a un periodo anterior y NO ha sido anotada en dicho periodo.'),
								('9',u'La operación corresponde a un periodo anterior y SI ha sido anotada en dicho periodo.')],string='Estado PLE',default='1')
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)