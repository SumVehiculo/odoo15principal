# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountCashFlowBook(models.Model):
	_name = 'account.cash.flow.book'
	_description = 'Account Cash Flow Book'

	grupo = fields.Char(string='Grupo')
	concepto = fields.Char(string='Concepto')
	account_id = fields.Many2one('account.account',string='Cuenta')
	fecha = fields.Date(string=u'Fecha')
	amount = fields.Float(string='Movimiento', digits=(64,2))
	semana = fields.Char(string='SEMANA')
	user_id = fields.Many2one('res.users',string='Usuario')