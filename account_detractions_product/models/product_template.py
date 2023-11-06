# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError



class Product_template(models.Model):
	_inherit = 'product.template'

	is_afecto_detraction =  fields.Boolean(string='Afecto a Detracción',copy=False)
