# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountCashFlow(models.Model):
	_name = 'account.cash.flow'
			
	name = fields.Char(string='Rubro',required=True)
	code = fields.Char(string='Codigo',size=6)
	group = fields.Char(string='Grupo')
	sequence = fields.Integer(string='Orden')

	def name_get(self):
		result = []
		for einv in self:
			result.append([einv.id,einv.code])
		return result