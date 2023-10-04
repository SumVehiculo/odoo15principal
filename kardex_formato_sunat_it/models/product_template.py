# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ProductTemplate(models.Model):
	_inherit = 'product.template'

	onu_code = fields.Many2one('einvoice.catalog.25',string='Codigo ONU')