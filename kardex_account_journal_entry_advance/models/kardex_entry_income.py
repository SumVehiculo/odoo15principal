# -*- coding: utf-8 -*-

from odoo import models, fields, api

class KardexEntryIncomeIt(models.Model):
	_name = 'kardex.entry.income.it'
	
	period_id = fields.Many2one('account.period',string=u'Periodo')
	move_ids = fields.One2many('account.move','kardex_income_id',string=u'Asientos')
	company_id = fields.Many2one('res.company',string='Compañia',required=True,default=lambda self: self.env.company,readonly=True)