# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError


class StockPickingType(models.Model):
	_inherit = "stock.picking.type"

	operation_kardex_id = fields.Many2one('type.operation.kardex',string='Tipo de Operacion SUNAT')