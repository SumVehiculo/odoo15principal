# -*- coding: utf-8 -*-
from openerp import models, fields, api
from odoo.exceptions import AccessError, UserError, ValidationError

class sale_order(models.Model):
	_inherit = 'sale.order'


	@api.model
	def create(self,vals):	
		t = super(sale_order,self).create(vals)
		t.verify_lista_precio_tarifa()
		return t


	def verify_lista_precio_tarifa(self):
		for i in self:
			if i.pricelist_id.id and i.pricelist_id.id != i.partner_id.property_product_pricelist.id:
				if not self.env.user.has_group("sale_discount_tarifa_group.group_sale_order_tarifa_restriction"):
					raise UserError("Campo Lista de Precios solo puede ser modificada por el grupo 'Manejo Lista de Precio Venta' ")

	def write(self,vals):
		t = super(sale_order,self).write(vals)
		if "pricelist_id" in vals:
			for i in self:
				if i.pricelist_id.id != i.partner_id.property_product_pricelist.id:
					if not i.env.user.has_group("sale_discount_tarifa_group.group_sale_order_tarifa_restriction"):
						raise UserError("Campo Lista de Precios solo puede ser modificada por el grupo 'Manejo Lista de Precio Venta' ")
		return t



class sale_order_line(models.Model):
	_inherit = 'sale.order.line'


	@api.model
	def create(self,vals):	
		t = super(sale_order_line,self).create(vals)
		t.verify_discount_no_cero()
		return t


	def verify_discount_no_cero(self):
		for i in self:
			if i.discount != 0:
				if not self.env.user.has_group("sale_discount_tarifa_group.group_sale_order_discount_restriction"):
					raise UserError("Campo Lista de Precios solo puede ser modificada por el grupo 'Manejo Descuento En Ventas'")

	def write(self,vals):
		t = super(sale_order_line,self).write(vals)
		if "discount" in vals:
			if not self.env.user.has_group("sale_discount_tarifa_group.group_sale_order_discount_restriction"):
				raise UserError("Campo Lista de Precios solo puede ser modificada por el grupo 'Manejo Descuento En Ventas'")
		return t
