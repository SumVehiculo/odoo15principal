# -*- coding: utf-8 -*-

from odoo import models, fields, api

class StockCatalog06(models.Model):
	_name = 'stock.catalog.06'
	_description = 'Stock Catalog 06'

	name = fields.Char(string='Descripcion')
	code = fields.Char(string='Codigo')

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