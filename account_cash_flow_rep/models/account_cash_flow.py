# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountCashFlow(models.Model):
	_inherit = 'account.cash.flow'

	grupo = fields.Selection([('1','SALDO INICIAL'),
							('2','INGRESO'),
							('3','EGRESO'),
							('4','FINANCIAMIENTO')],default='1',string=u'Grupo (*)')

	code = fields.Char(string='Codigo',size=6,required=True)

	def name_get(self):
		result = []
		for einv in self:
			name = einv.code + ' ' + einv.name
			result.append((einv.id, name))
		return result