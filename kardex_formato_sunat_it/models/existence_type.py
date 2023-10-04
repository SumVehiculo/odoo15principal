# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ExistenceType(models.Model):
	_name = 'existence.type'

	name = fields.Char(string='Descripcion',required=True)
	code = fields.Char(string='Nro.')

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
			result.append([einv.id,einv.code])
		return result