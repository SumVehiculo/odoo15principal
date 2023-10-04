# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from datetime import date
from odoo import api, fields, models, _
from odoo.tools import format_amount


class ProductTemplate(models.Model):
	_inherit = 'product.template'

	surrender_ok = fields.Boolean(string="Sirve para Rendiciones")