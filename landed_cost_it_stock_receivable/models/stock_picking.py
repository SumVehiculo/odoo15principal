# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError

class StockPicking(models.Model):
	_inherit = 'stock.picking'

	landed_receivable_id = fields.Many2one('landed.cost.it',string='Gasto Vinculado Origen')