# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class ResCurrencyRate(models.Model):
	_inherit = "res.currency.rate"

	purchase_type = fields.Float(string='Tipo Compra',digits=(16, 3))
	sale_type = fields.Float(string='Tipo Venta',digits=(16, 3))