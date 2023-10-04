# -*- coding: utf-8 -*-

from odoo import fields, models

class ProductTemplate(models.Model):
	_inherit = "product.template"

	is_landed_cost = fields.Boolean(string='Se usa en Gasto Vinculado',default=False)
	type_landed_cost_id = fields.Many2one('landed.cost.it.type',string='Tipo G.V.',copy=False)