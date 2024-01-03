# -*- coding: utf-8 -*-

from odoo import api, fields, models, _ , exceptions
from odoo.exceptions import UserError



class StockPicking(models.Model):
	_inherit = "stock.picking"

	@api.model
	def create(self, vals):
		t = super(StockPicking, self).create(vals)
		if t.kardex_date:
			if t.state == 'draft':
				raise UserError('No tiene permisos de Edicion del Kardex, ya que el Albarán esta en estado borrador')
		return t