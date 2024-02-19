# -*- coding: utf-8 -*-
from odoo import SUPERUSER_ID, _, api, fields, models
from odoo.exceptions import UserError


class PickingType(models.Model):
	_inherit = 'stock.picking.type'


	account_analytic_type = fields.Boolean(string="Cuentas analiticas obligatorias", defaul=False)

class StockPicking(models.Model):
	_inherit = 'stock.picking'



	def button_validate(self):
		for sp in self:
			if self.picking_type_id:
				if self.picking_type_id.account_analytic_type == True:
					for sm in self.move_ids_without_package:
						if not sm.analytic_account_id:
							raise UserError(f'El producto {sm.product_id.name} No tiene una cuenta analitica agregada')
						if not sm.analytic_tag_id:
							raise UserError(f'El producto {sm.product_id.name} No tiene una etiqueta analitica agregada')
		test = super(StockPicking,self).button_validate()
		return test