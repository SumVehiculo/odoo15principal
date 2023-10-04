# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountCashFlowBookAdvance(models.Model):
	_name = 'account.cash.flow.book.advance'
	_description = 'Account Cash Flow Book Advance'

	journal_id = fields.Many2one('account.journal',string='Diario')
	voucher = fields.Char(string='Voucher')
	fecha = fields.Date(string=u'Fecha')
	glosa = fields.Char(string='Glosa')
	account_id = fields.Many2one('account.account',string='Cuenta')
	amount = fields.Float(string='Movimiento', digits=(64,2))
	grupo = fields.Char(string='Grupo')
	concepto = fields.Char(string='Concepto')
	user_id = fields.Many2one('res.users',string='Usuario')