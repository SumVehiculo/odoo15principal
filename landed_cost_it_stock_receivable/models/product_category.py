# -*- coding: utf-8 -*-

from odoo import fields, models

class ProductCategory(models.Model):
	_inherit = "product.category"

	property_account_stock_receivable_categ_id = fields.Many2one('account.account', company_dependent=True,
		string="Cuenta para Existencias por Recibir",
		domain="['&', '&', '&', ('deprecated', '=', False), ('internal_type','=','other'), ('company_id', '=', current_company_id), ('is_off_balance', '=', False)]")