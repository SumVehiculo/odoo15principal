# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountTypeIt(models.Model):
	_inherit = 'account.type.it'

	total_code_sunat = fields.Char(string='Total SUNAT',size=6)