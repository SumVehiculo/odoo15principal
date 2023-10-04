# -*- coding: utf-8 -*-

from ast import Pass
from pickle import PicklingError
from shutil import move
from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo import tools

class product_template(models.Model):
	_inherit = 'product.template'
	
	def unlink(self):
		if self.env.user.has_group("product_template_restriction.group_product_template_restriction"):
			t = super(product_template,self).unlink()
			return t
		else:
			raise UserError("No Tiene Los Permisos de 'Manejo Creacion de Productos'")

	@api.model
	def create(self,vals):
		if self.env.user.has_group("product_template_restriction.group_product_template_restriction"):
			t = super(product_template,self).create(vals)
			return t
		else:
			raise UserError("No Tiene Los Permisos de 'Manejo Creacion de Productos'")
		   
	def write(self,vals):
		if self.env.user.has_group("product_template_restriction.group_product_template_restriction"):
			t = super(product_template,self).write(vals)
			return t
		else:
			if 'permiso_especial_prod' in self.env.context:
				t = super(product_template,self).write(vals)
				return t
			else:
				if 'standard_price' in vals and len(vals)==1:
					pass
				else:
					raise UserError("No Tiene Los Permisos de 'Manejo Creacion de Productos'")
			

class product_product(models.Model):
	_inherit = 'product.product'
	
	def unlink(self):
		if self.env.user.has_group("product_template_restriction.group_product_template_restriction"):
			t = super(product_product,self).unlink()
			return t
		else:
			raise UserError("No Tiene Los Permisos de 'Manejo Creacion de Productos'")

	@api.model
	def create(self,vals):
		if self.env.user.has_group("product_template_restriction.group_product_template_restriction"):
			t = super(product_product,self).create(vals)
			return t
		else:
			raise UserError("No Tiene Los Permisos de 'Manejo Creacion de Productos'")
		   
	def write(self,vals):
		if self.env.user.has_group("product_template_restriction.group_product_template_restriction"):
			t = super(product_product,self).write(vals)
			return t
		else:
			if 'permiso_especial_prod' in self.env.context:
				t = super(product_product,self).write(vals)
				return t
			else:
				if 'standard_price' in vals and len(vals)==1:
					pass
				else:
					raise UserError("No Tiene Los Permisos de 'Manejo Creacion de Productos'")


class purchase_order(models.Model):
	_inherit = 'purchase.order' 
	
	def _add_supplier_to_product(self):
		if self.env.user.has_group("product_template_restriction.group_product_template_restriction"):
			t = super(purchase_order, self)._add_supplier_to_product()
		else:
			grupo_editor = self.env.ref('product_template_restriction.group_product_template_restriction')
			grupo_editor.sudo().write({'users':[(4, self.env.user.id)]
												   })
			t = super(purchase_order, self)._add_supplier_to_product()
			grupo_editor.sudo().write({'users':[(3, self.env.user.id)]
												   })
		return t

