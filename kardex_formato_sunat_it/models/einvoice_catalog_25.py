# -*- coding: utf-8 -*-

from odoo import models, fields, api

class EinvoiceCatalog25(models.Model):
	_name = 'einvoice.catalog.25'

	name = fields.Char(string='Nombre')
	code = fields.Char(string='Codigo',size=8)

	@api.model
	def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
		args = args or []
		einvoice_ids = []
		if name:
			einvoice_ids = self._search(['|',('name', '=', name),('code','=',name)] + args, limit=limit, access_rights_uid=name_get_uid)
		if not einvoice_ids:
			einvoice_ids = self._search(['|',('name', operator, name),('code', operator, name)] + args, limit=limit, access_rights_uid=name_get_uid)
		return einvoice_ids