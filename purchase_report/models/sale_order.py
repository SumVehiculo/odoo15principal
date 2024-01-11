# -*- coding: utf-8 -*-

from odoo import models, fields, api

class purchase_order_line(models.Model):
	_inherit = 'purchase.order.line'
	
	cod_proveedor = fields.Char('cod_sum', compute='compute_cod_proveedor')
	
	@api.depends('product_id')
	def compute_cod_proveedor(self):
		for i in self:
			i.cod_proveedor = ""
			for lp in i.product_id.seller_ids:
				if lp.name.id == i.order_id.partner_id.id:
					i.cod_proveedor = lp.product_code
            