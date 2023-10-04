# -*- coding:utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError

class AccountAccount(models.Model):
	_inherit = 'account.account'

	account_cash_flow_id = fields.Many2one('account.cash.flow',string='Tipo Flujo de Caja')