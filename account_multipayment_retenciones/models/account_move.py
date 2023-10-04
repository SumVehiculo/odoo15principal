# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class AccountMove(models.Model):
	_inherit = 'account.move'
	
	def button_draft(self):
		for move in self:
			multip = self.env['multipayment.advance.it'].search([('asiento_id','=',move.id)])
			if multip:
				raise UserError('No puede restablecer a borrador una factura que fue creada desde un Pago Múltiple, debe editar desde el Pago Múltiple %s'%(multip.name))
		return super(AccountMove, self).button_draft()