# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class stock_picking(models.Model):
	_inherit = 'stock.picking'



	def add_costos(self):
		for i in self:
			if i.state =='done':				
				for l in self.env['stock.move'].search([('picking_id','=',i.id)]):
					if l.location_id.usage == 'inventory' and l.location_dest_id.usage == 'internal':

						line_val = self.env['stock.valuation.layer'].search([('product_id','=',l.product_id.id),('stock_move_id','=',l.id)])
						if len(line_val)>0:
							line_val.unit_cost = l.price_unit_it
							line_val.value = l.price_unit_it * line_val.quantity
						else:
							data = {
								'product_id':l.product_id.id,
								'unit_cost':l.price_unit_it,
								'quantity':l.product_uom_qty,
								'value':l.price_unit_it*l.product_uom_qty,
								'company_id':i.company_id.id,
								'stock_move_id':l.id,
							}
							line_val = self.env['stock.valuation.layer'].create(data)

						costo_actual = 0
						cantidad_actual = 0
						for ij in self.env['stock.valuation.layer'].search([('product_id','=',l.product_id.id)]):
							costo_actual += ij.value
							cantidad_actual += ij.quantity	
						self.env.cr.execute("""
							select id from ir_property 
							where name = 'standard_price' and company_id = """ + str(self.env.company.id)+ """ and res_id = 'product.product,"""+str(l.product_id.id)+"""' 
							""") 
						ver = self.env.cr.fetchall()
						if len(ver)==0:
							self.env['ir.property'].create({
								'name':'standard_price',
								'company_id':i.company_id.id,
								'res_id':'product.product,'+str(l.product_id.id),
								'value_float':costo_actual / cantidad_actual if cantidad_actual!=0 else 0,
								'type':'float',
								'fields_id':2848,
								})
						else:
							self.env.cr.execute("""
							update ir_property set value_float = """ + str(costo_actual / cantidad_actual if cantidad_actual!=0 else 0) + """
							where name = 'standard_price' and company_id = """ + str(self.env.company.id)+ """ and res_id = 'product.product,"""+str(l.product_id.id)+"""' 
							""") 
			
