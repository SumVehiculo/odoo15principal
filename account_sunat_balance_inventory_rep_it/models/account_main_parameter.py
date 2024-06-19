# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountMainParameter(models.Model):
	_inherit = 'account.main.parameter'
	
	use_balance_inventory_kardex = fields.Boolean(string='Usar Kardex',default=False)