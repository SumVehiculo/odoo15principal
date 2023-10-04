# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ResPartner(models.Model):
	_inherit = 'res.partner'
	
	@api.model
	def _commercial_fields(self):
		res = super()._commercial_fields()
		res.remove("l10n_latam_identification_type_id")
		res.remove("vat")
		return res