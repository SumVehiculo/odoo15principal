# -*- coding: utf-8 -*-

from odoo import models, fields, api

class EinvoiceCatalogPayment(models.Model):
	_name = 'einvoice.catalog.payment'
			
	name = fields.Char(string='Descripcion',required=True)
	code = fields.Char(string='Codigo')
	pse_code = fields.Char(string='Codigo de Facturador', size=5)

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
			result.append([einv.id,einv.name])
		return result