# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo import tools



class UpdateExpectedDateWizard(models.TransientModel):
	_name = 'update.account.picking.wizard'
	_description = "Actualizacion de Facturas en albaranes"

	picking_id = fields.Many2one('stock.picking', string='Transferencia')
	account_picking = fields.Many2one('account.move',string='Factura')


	def save_account_picking_it(self):
		for sav in self:
			if sav.picking_id:
				sav.picking_id.invoice_id = sav.account_picking.id

class StockPicking(models.Model):
	_inherit = 'stock.picking'

	vs_wizard = fields.Boolean(string='Campo Computado', compute='_compute_vs_wizard')

	@api.depends('name','state')
	def _compute_vs_wizard(self):
		for record in self:
			user = self.env.user
			record.vs_wizard = user.has_group('account_picking_edit.group_edit_add_account_move_by_wizard')



	def update_account_picking_wizard_it(self):
		for wi in self:
			if wi.vs_wizard and wi.state not in ('cancel','draft'):
			# if wi.vs_wizard and wi.state == 'done':
				context = {
					'default_picking_id': wi.id, 
					'default_account_picking': wi.invoice_id.id if wi.invoice_id else False, 
				}
				return {
					'type': 'ir.actions.act_window',
					'view_mode': 'form',
					'res_model': 'update.account.picking.wizard',
					'views': [(False, 'form')],
					'view_id': False,
					'target': 'new',
					'context': context,
				}
			else:
				raise UserError('No puede ingresar si no se encuentra en el grupo, o la transferencia se encuentra en Borrador o Cancelado')