# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools

class PurchaseOrderLine(models.Model):
	_inherit = 'purchase.order.line'
	
	purchase_date_landed = fields.Datetime(related='order_id.date_order',string='Fecha Pedido')
	name_po_landed = fields.Char(related='order_id.name',string='Pedido')
	partner_id_landed = fields.Many2one(related='order_id.partner_id',string='Socio')
	tc_landed = fields.Float(string='TC',compute='compute_tc_landed',digits=(12,4),store=True)
	price_total_signed_landed = fields.Float(string='Total Soles',compute='compute_price_total_signed_landed',digits=(64,2),store=True)
	currency_id_landed = fields.Many2one(related='order_id.currency_id',string='Moneda')
	is_landed = fields.Boolean(related='product_id.product_tmpl_id.is_landed_cost',string='Usa GV')

	@api.depends('order_id.date_order')
	def compute_tc_landed(self):
		for line in self:
			currency = self.env.ref('base.USD')
			tc = self.env['res.currency.rate'].search([('name','=',line.order_id.date_order.date()),('currency_id','=',currency.id)],limit=1)
			line.tc_landed = tc.sale_type if tc else 1
	
	@api.depends('tc_landed')
	def compute_price_total_signed_landed(self):
		for line in self:
			if line.order_id.currency_id.name != 'PEN':
				line.price_total_signed_landed = line.price_subtotal * line.tc_landed
			else:
				line.price_total_signed_landed = line.price_subtotal