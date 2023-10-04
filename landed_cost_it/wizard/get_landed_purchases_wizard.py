# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _

class GetLandedPurchases(models.TransientModel):
	_name = "get.landed.purchases.wizard"
	
	landed_id = fields.Many2one('landed.cost.it',string='Gasto Vinculado')
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	purchases_ids = fields.Many2many('purchase.order.line',string=u'Purchases', required=True,
	domain="[('display_type','=',False),('state','in',['purchase','done']),('is_landed','=',True),('company_id','=',company_id)]")
		
	def insert(self):
		vals=[]
		for purchase in self.purchases_ids:
			val = {
				'landed_id': self.landed_id.id,
				'purchase_id': purchase.id,
				'purchase_date': purchase.order_id.date_order.date(),
				'name': purchase.order_id.name,
				'partner_id': purchase.order_id.partner_id.id,
				'product_id': purchase.product_id.id,
				'price_total_signed': purchase.price_total_signed_landed,
				'tc': purchase.tc_landed,
				'currency_id': purchase.order_id.currency_id.id,
				'price_total': purchase.price_subtotal,
				'company_id': purchase.company_id.id,
			}
			vals.append(val)
		self.env['landed.cost.purchase.line'].create(vals)
		self.landed_id._change_flete()