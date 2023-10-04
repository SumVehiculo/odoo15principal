# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class GlenModelUpdate(models.Model):
	_name = "glen.model_update"
	_description = "holas"

	@api.model
	def function_remove_permissions_it(self):
		grupo = self.env['res.groups'].search([('name','=','Editor Catalogos')]).id

		model = self.env['ir.model'].search([('model','=','res.partner')],limit=1)
		for access in model.access_ids:
			if access.group_id.id != grupo.id:
				access.unlink()

		model = self.env['ir.model'].search([('model','=','product.product')],limit=1)
		for access in model.access_ids:
			if access.group_id.id != grupo.id:
				access.unlink()
		
		model = self.env['ir.model'].search([('model','=','product.template')],limit=1)
		for access in model.access_ids:
			if access.group_id.id != grupo.id:
				access.unlink()
		
		model = self.env['ir.model'].search([('model','=','product.category')],limit=1)
		for access in model.access_ids:
			if access.group_id.id != grupo.id:
				access.unlink()
		
		model = self.env['ir.model'].search([('model','=','account.account')],limit=1)
		for access in model.access_ids:
			if access.group_id.id != grupo.id:
				access.unlink()
		
		model = self.env['ir.model'].search([('model','=','account.journal')],limit=1)
		for access in model.access_ids:
			if access.group_id.id != grupo.id:
				access.unlink()
		
		model = self.env['ir.model'].search([('model','=','account.analytic.account')],limit=1)
		for access in model.access_ids:
			if access.group_id.id != grupo.id:
				access.unlink()