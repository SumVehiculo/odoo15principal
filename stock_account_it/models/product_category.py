# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class ProductCategory(models.Model):
	_inherit = 'product.category'

	stock_catalog_05_id = fields.Many2one('stock.catalog.05',string="Catalogo Existencias")
	table_13_sunat = fields.Selection([('1','Naciones'),('3',u'GS1 (EAN-UCC)'),('9','OTROS')],string='Tabla 13')