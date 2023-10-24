# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class res_partner(models.Model):
	_inherit = 'res.partner'

	@api.model
	def create(self, vals):
		res = super(res_partner,self).create(vals)
		for i in res:
			if i.parent_id.id:
				return res
			if not i.vat:
				raise UserError(u'Falta llenar Número identificación')
			if not i.email:
				raise UserError(u'Falta llenar Correo electrónico')
		return res

	def write(self, vals):
		res = super(res_partner,self).write(vals)
		for i in self:
			if i.parent_id.id:
				return res
			if not i.vat:
				raise UserError(u'Falta llenar Número identificación')
			if not i.email:
				raise UserError(u'Falta llenar Correo electrónico')
		return res
