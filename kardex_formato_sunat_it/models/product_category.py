# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class ProductCategory(models.Model):
	_inherit = 'product.category'

	code = fields.Char(string="Codigo",size=40)
	existence_type_id = fields.Many2one('existence.type',string="Codigo Sunat")