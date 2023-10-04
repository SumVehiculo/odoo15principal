# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError

class PurchaseOrder(models.Model):
	_inherit = 'purchase.order'

	landed_cost_id = fields.Many2one('landed.cost.it',string='Gasto Vinculado',copy=False)

	def create_landed_cost(self):
		if self.state not in ('purchase','done'):
			raise UserError('Solo se puede crear el Gasto Vinculado si el Pedido esta confirmado.')
		landed = self.env['landed.cost.it'].create({
			'date_kardex': fields.Datetime.now(),
			'company_id': self.company_id.id,
			'purchase_origin_id': self.id
		})
		self.landed_cost_id = landed.id
		for p in self.picking_ids:
			p.landed_cost_id = landed.id

		return {
			'view_mode': 'form',
			'view_id': self.env.ref('landed_cost_it.view_landed_cost_it_form').id,
			'res_model': 'landed.cost.it',
			'type': 'ir.actions.act_window',
			'res_id': landed.id,
		}
	
	def show_landed_cost(self):
		self.ensure_one()
		action = self.env.ref('landed_cost_it.action_landed_cost_it').read()[0]
		domain = [('id', 'in', [self.landed_cost_id.id])]
		context = dict(self.env.context, default_invoice_id=self.id)
		views = [(self.env.ref('landed_cost_it.view_landed_cost_it_tree').id, 'tree'), (False, 'form'), (False, 'kanban')]
		return dict(action, domain=domain, context=context, views=views)