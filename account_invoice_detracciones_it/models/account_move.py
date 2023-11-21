# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class AccountMove(models.Model):
	_inherit = 'account.move'

	name_move_detraccion = fields.Char(string=u'Nombre Detracción',copy=False)
	diario_move_detraccion = fields.Many2one('account.journal',string=u'Nombre Diario')
	fecha_move_detraccion = fields.Date(string='Periodo')

	def get_state_button_detraction(self):
		for i in self:
			if i.state == 'posted' or i.payment_state == 'paid':
				if i.move_detraccion_id.id:
					i.state_detraction_button = 1
				else:
					i.state_detraction_button = 2
			else:
				i.state_detraction_button = 3

	move_detraccion_id = fields.Many2one('account.move',string=u'Asiento Detracción',copy=False)
	state_detraction_button = fields.Integer(string='Estado Boton', default=3,compute=get_state_button_detraction)

	@api.onchange('detraction_percent_id','amount_total')
	def onchange_detraction_percent_id(self):
		for move in self:
			if move.detraction_percent_id:
				move.detra_amount = round(move.amount_total * move.detraction_percent_id.percentage,2)
			else:
				move.detra_amount = 0

	def action_post(self):
		res = super(AccountMove, self).action_post()
		for move in self:
			move.onchange_detraction_percent_id()
		return res

	def button_cancel(self):
		if self.move_detraccion_id.id:
			if self.move_detraccion_id.state != 'draft':
				self.move_detraccion_id.button_cancel()
				self.move_detraccion_id.line_ids.remove_move_reconcile()
			self.move_detraccion_id.line_ids.unlink()
			self.move_detraccion_id.name = "/"
			self.move_detraccion_id.unlink()
			self.name_move_detraccion = None
		return super(AccountMove,self).button_cancel()

	def remove_detraccion_gastos(self):
		if self.move_detraccion_id.id:
			if self.move_detraccion_id.state != 'draft':
				self.move_detraccion_id.button_cancel()
				self.move_detraccion_id.line_ids.remove_move_reconcile()
			self.move_detraccion_id.line_ids.unlink()
			self.move_detraccion_id.name = "/"
			self.move_detraccion_id.unlink()
			self.name_move_detraccion = None
		return True

	def create_detraccion_gastos(self):
		###SE CAMBIO POR FUSION
		context = {'invoice_id': self.id,'default_fecha': self.date ,
		'default_monto':self.detra_amount}
		return {
				'type': 'ir.actions.act_window',
				'name': "Generar Detracción",
				'view_type': 'form',
				'view_mode': 'form',
				'context': context,
				'res_model': 'account.detractions.wizard',
				'target': 'new',
		}
