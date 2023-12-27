# -*- coding: utf-8 -*-

from odoo import fields, models, tools

class ReportStockQuantity(models.Model):
    _inherit = 'report.stock.quantity'
    
    product_name = fields.Char(related='product_id.name', string="Producto", readonly=True)
    product_code = fields.Char(related='product_id.default_code', string="Referencia del producto", readonly=True)