# -*- coding: utf-8 -*-
from openerp import models, fields, api
from odoo.exceptions import AccessError, UserError, ValidationError

class res_partner(models.Model):
	_inherit = 'res.partner'


#	@api.model
#	def create(self,vals):
#		t = super(gastos_vinculados_it,self).create(vals)
#		t.check_plazo_group_permision()
#		return t
	
	def write(self,vals):
		t = super(res_partner,self).write(vals)
		if "user_id" in vals or "property_payment_term_id" in vals or "property_product_pricelist" in vals:
			for i in self:
				if not i.parent_id.id:
					if not i.env.user.has_group("res_partner_tarifa_plazo_group.group_res_partner_tarifa_plazos_vendedor_restriction"):
						raise UserError("Campos Vendedor, Plazos de pago y Lista de Precios solo puede ser modificada por el grupo 'Manejo Tarifa y Plazos de Pago En Contactos' ")
		return t
