# -*- coding: utf-8 -*-

from odoo import models, fields, api

class LandedCostItType(models.Model):
	_name = 'landed.cost.it.type'
	_description = 'Landed Cost It Type'

	code = fields.Char(string='Codigo',required=True)
	name = fields.Char(string='Descripcion',required=True)

	_sql_constraints = [
		('code_uniq', 'unique(code)',
		 'Ya existe el Código en el sistema.'),
	]

	@api.model
	def name_search(self, name, args=None, operator='ilike', limit=100):
		args = args or []
		recs = self.browse()
		if name:
			recs = self.search(['|',('code', '=', name),('name','=',name)] + args, limit=limit)
		if not recs:
			recs = self.search(['|',('code', operator, name),('name',operator,name)] + args, limit=limit)
		return recs.name_get()

	def name_get(self):
		result = []
		for einv in self:
			name = einv.code + ' ' + einv.name
			result.append((einv.id, name))
		return result