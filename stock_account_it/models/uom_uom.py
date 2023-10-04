# -*- coding: utf-8 -*-

from odoo import api, fields, models

class UomUom(models.Model):
    _inherit = 'uom.uom'

    stock_catalog_06_id = fields.Many2one('stock.catalog.06',string="Codigo Sunat")