# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ProductionIncomeIt(models.Model):
	_name = 'production.income.it'
	
	period_id = fields.Many2one('account.period',string=u'Periodo')
	move_id = fields.Many2one('account.move',string=u'Asiento')
	#move_return_id = fields.Many2one('account.move',string=u'Asiento Devolución')
	company_id = fields.Many2one('res.company',string='Compañia',required=True,default=lambda self: self.env.company,readonly=True)