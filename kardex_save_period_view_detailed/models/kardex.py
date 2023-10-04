# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class kardex_save(models.Model):
	_inherit = 'kardex.save'

	detalles_count_view = fields.Integer(string="Detalles",compute="tre_get_details_view")

	@api.depends("lineas")
	def tre_get_details_view(self):
		for i in self:
			i.detalles_count_view = len(i.lineas)

	def action_get_detailed_tree_view_sr(self):
		action = self.env.ref('kardex_save_period_view_detailed.kardex_save_period_new_action').read()[0]
		#action['context'] = {
			#'default_res_model': self._name
		#}
		action['domain'] = [('save_id', 'in', self.ids)]
		return action