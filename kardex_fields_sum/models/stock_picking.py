# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError

class StockPicking(models.Model):
	_inherit = "stock.picking"

	@api.onchange('picking_type_id')
	def onchange_picking_type_id_sum(self):
		for p in self:		
			if p.picking_type_id.operation_kardex_id:
				p.type_operation_sunat_id = p.picking_type_id.operation_kardex_id.id

	@api.model_create_multi
	def create(self, vals_list):
		rslt = super(StockPicking, self).create(vals_list)
		if rslt.picking_type_id.operation_kardex_id:
			rslt.type_operation_sunat_id = rslt.picking_type_id.operation_kardex_id.id
		return rslt