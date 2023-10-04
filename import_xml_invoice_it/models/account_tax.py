# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountTax(models.Model):
	_inherit = 'account.tax'

	code_fe = fields.Char(string='F.E. Codigo de Impuesto',help="Para importar Facturas XML")