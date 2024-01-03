# -*- coding: utf-8 -*-

from odoo import api, fields, models, _ , exceptions
from odoo.exceptions import UserError



class StockPicking(models.Model):
	_inherit = "stock.picking"

	@api.model
	def create(self, vals):
		if not self.kardex_date:
			if self.state == 'draft':
				raise('No tiene permisos de Edicion del Kardex, ya que el Albarán esta en estado borrador')
		t = super(StockPicking, self).create(vals)
		return t