# -*- coding: utf-8 -*-
from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError

class account_move(models.Model):

	_inherit = 'account.move'

	check_vali_detraction = fields.Boolean('VALIDADOR DETRACCIÓN', compute='_compute_check_vali_detraction')


	def write(self, vals):
		res = super(account_move,self).write(vals)
		for i in self:
			if 'tax_country_id' in vals:
				i._onchange_check_vali_detraction()
		return res

	@api.model
	def create(self, vals):
		res = super(account_move,self).create(vals)		
		for i  in res:
			i._onchange_check_vali_detraction()
		return res
	

	def _onchange_check_vali_detraction(self):
		for i in self:
			if i.check_vali_detraction:
				i.linked_to_detractions = True
				i.detraction_percent_id =  self.env['detractions.catalog.percent'].sudo().search([('code','=','012')],limit=1).id
			else:
				i.linked_to_detractions = False

	@api.depends('invoice_line_ids','invoice_line_ids.product_id','amount_total')
	def _compute_check_vali_detraction(self):
		for i in self:	
			i.check_vali_detraction = False		
			for line in i.invoice_line_ids.filtered(lambda l: l.product_id.product_tmpl_id.is_afecto_detraction):
				if abs(i.amount_total) > self.env['account.main.parameter'].sudo().search([('company_id','=',self.env.company.id)],limit=1).max_detracion:
					i.check_vali_detraction = True


	def action_post(self):
		result = super(account_move,self).action_post()
		for i in self:
			i.funtion_detraction()           
		return result
	
	def funtion_detraction(self):
			for i in self:				
				if i.linked_to_detractions:                
					if not i.type_op_det:
						raise UserError(u'El campo "Tipo de Operación" no esta configurado en la pestaña SUNAT')
					if not i.detraction_percent_id:
						raise UserError(u'El campo "Bien o Servicio" no esta configurado en la pestaña SUNAT')
					if not i.detra_amount:
						raise UserError(u'El campo "Monto" no esta configurado en la pestaña SUNAT')
					
					context = {
						'invoice_id': i.id,
						'default_fecha': i.date,
						'default_monto': i.detra_amount
						}
					detraccion = self.env['account.detractions.wizard'].with_context(context).create({
							'fecha': i.date,
							'monto': i.detra_amount
						})
					if detraccion:
						detraccion.generar()
	
