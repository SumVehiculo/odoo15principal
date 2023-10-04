# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountMove(models.Model):
	_inherit = 'account.move'
	
	kardex_income_id = fields.Many2one('kardex.entry.income.it',string='DETALLE INGRESOS')
	kardex_outcome_id = fields.Many2one('kardex.entry.outcome.it',string='DETALLE SALIDAS')