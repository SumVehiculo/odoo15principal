# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountMainParameter(models.Model):
	_inherit = 'account.main.parameter'
	
	cash_account_prefix_ids = fields.Many2many('account.account', 'account_main_parameter_cash_prefix_rel', string='Cuentas para Cajas')
	bank_account_prefix_ids = fields.Many2many('account.account', 'account_main_parameter_bank_prefix_rel', string='Cuentas para Bancos')