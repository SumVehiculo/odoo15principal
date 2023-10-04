# -*- coding: utf-8 -*-
from odoo import models, fields, api
import base64

class stock_move_line(models.Model):
	_inherit = 'stock.move.line'

	price_unit_it = fields.Float('Precio Unitario')

class mrp_production(models.Model):
	_inherit = 'mrp.production'

	def calcular_costos(self):
		for i in self:
			total = 0
			for linex in i.move_raw_ids:
				total += linex.product_uom_qty * linex.price_unit_it

			for linet in i.finished_move_line_ids:
				linet.move_id.price_unit_it = total / linet.move_id.product_uom_qty
				linet.price_unit_it = total / linet.qty_done

