# -*- coding: utf-8 -*-
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
import time
import odoo.addons.decimal_precision as dp
from openerp.osv import osv
import base64
from odoo import models, fields, api
import codecs
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
def install(package):
	subprocess.check_call([sys.executable, "-m", "pip", "install", package])

try:
	import openpyxl
except:
	install('openpyxl==3.0.5')

from openpyxl.styles import Border, Side, PatternFill, Font, GradientFill, Alignment
from openpyxl.styles.borders import Border, Side, BORDER_THIN
from openpyxl import Workbook
values = {}
from openpyxl.utils import get_column_letter
from openpyxl.cell import WriteOnlyCell
values = {}

class kardex_vs_quant_view(models.TransientModel):
	_name = 'kardex.vs.quant.view'

	motivo = fields.Char('Motivo')
	product_id = fields.Many2one('product.product','Producto')
	lot_id = fields.Many2one('stock.production.lot','Lote')
	location_id = fields.Many2one('stock.location','Almacen')
	qty_odoo = fields.Float('Cantidad Odoo')
	qty_reservado_odoo = fields.Float('Reservado Odoo')
	qty_kardex = fields.Float('Cantidad Kardex')
	qty_reservado_kardex = fields.Float('Reservado Kardex')


class kardex_vs_quant_wizard(models.TransientModel):
	_name = 'kardex.vs.quant.wizard'

	def actualizar_diferencia(self):
		self.env.cr.execute("""
		update stock_quant set quantity = round(quantity::numeric,8) where round(quantity::numeric,8)!= quantity and location_id in ( select id from stock_location where usage='internal' );
		update stock_quant set reserved_quantity = round(reserved_quantity::numeric,8) where round(reserved_quantity::numeric,8)!= reserved_quantity and location_id in ( select id from stock_location where usage='internal' );
		update stock_move_line set product_uom_qty= round(product_uom_qty,8) , product_qty = round(product_qty,8) where state in ('partially_available','assigned');
		""")

		x = self.env['stock.balance.report.lote.wizard'].create({})
		x.get_stock_lote()
		
		t = self.env['stock.balance.report.lote'].sudo().search([])
		rpta = ""
		for i in t:
			lote = self.env['stock.quant'].sudo().search([('product_id','=',i.producto.id), ('lot_id','=',i.lote.id), ('location_id','=',i.almacen.id) ])	
			if len(lote)>0:
					total=0
					reservado = 0
					for l in lote:
						total+= l.quantity
						reservado+= l.reserved_quantity
					if i.entrada!= total or i.reservado != reservado:
						self.env.cr.execute(""" 
							update stock_quant set  quantity = """ + str(i.entrada)+ """ , reserved_quantity = """ + str(i.reservado)+ """  where id = """ +str(lote.id)+ """
						""")
				
			else:
				
				self.env['stock.quant'].sudo().create({
					'company_id': self.env.company.id,
					'location_id':i.almacen.id,
					'product_id':i.producto.id,
					'lot_id': i.lote.id,
					'quantity':i.entrada,
					'available_quantity':i.entrada,
					'reserved_quantity':i.reservado,
					'product_uom_id':i.producto.uom_id.id,
				})









		t = self.env['stock.quant'].sudo().search([('company_id','=',self.env.company.id),('location_id.usage','=','internal')])
		for i in t:
			lote = self.env['stock.balance.report.lote'].sudo().search([('producto','=',i.product_id.id), ('lote','=',i.lot_id.id), ('almacen','=',i.location_id.id)])	
			if len(lote)==0:
				
				self.env.cr.execute("""			
					delete from stock_quant where id = """ +str(i.id)+ """		
				
				""")




		t = self.env['stock.quant'].sudo().search([('product_id.tracking','=','serial'),('location_id.usage','in',('transit','internal'))])
		for l in t:
			otro = self.env['stock.quant'].sudo().search([('product_id.id','=',l.product_id.id),('lot_id','=',l.lot_id.id),('location_id.usage','in',('customer','supplier'))])
			for n in otro:
				if n.quantity >0:
				
					self.env.cr.execute("""
						
						delete from stock_quant where id = """ +str(n.id)+ """
					
					
					""")






	def mostrar_diferencia(self):
		self.env['kardex.vs.quant.view'].search([]).unlink()

		x = self.env['stock.balance.report.lote.wizard'].create({})
		x.get_stock_lote()
		
		t = self.env['stock.balance.report.lote'].sudo().search([])
		rpta = ""
		for i in t:
			lote = self.env['stock.quant'].sudo().search([('product_id','=',i.producto.id), ('lot_id','=',i.lote.id), ('location_id','=',i.almacen.id) ])	
			if len(lote)>0:
					total=0
					reservado = 0
					for l in lote:
						total+= l.quantity
						reservado+= l.reserved_quantity
					if i.entrada!= total or i.reservado != reservado:
						self.env['kardex.vs.quant.view'].create({
							'motivo':'Descuadre de Monto',
							'product_id':i.producto.id,
							'lot_id':i.lote.id,
							'location_id': i.almacen.id,
							'qty_odoo':total,
							'qty_reservado_odoo':reservado,
							'qty_kardex':i.entrada,
							'qty_reservado_kardex':i.reservado,
							})
			else:				
				self.env['kardex.vs.quant.view'].create({
					'motivo':'No existe Quant',
					'product_id':i.producto.id,
					'lot_id':i.lote.id,
					'location_id': i.almacen.id,
					'qty_odoo':0,
					'qty_reservado_odoo':0,
					'qty_kardex':i.entrada,
					'qty_reservado_kardex':i.reservado,
					})



		t = self.env['stock.quant'].sudo().search([('company_id','=',self.env.company.id),('location_id.usage','=','internal')])
		for i in t:
			lote = self.env['stock.balance.report.lote'].sudo().search([('producto','=',i.product_id.id), ('lote','=',i.lot_id.id), ('almacen','=',i.location_id.id)])	
			if len(lote)==0:			
				self.env['kardex.vs.quant.view'].create({
					'motivo':'No existe en Kardex',
					'product_id':i.product_id.id,
					'lot_id':i.lot_id.id,
					'location_id': i.location_id.id,
					'qty_odoo':i.quantity,
					'qty_reservado_odoo':i.reserved_quantity,
					'qty_kardex':0,
					'qty_reservado_kardex':0,
					})





		t = self.env['stock.quant'].sudo().search([('product_id.tracking','=','serial'),('location_id.usage','in',('transit','internal'))])
		for l in t:
			otro = self.env['stock.quant'].sudo().search([('product_id.id','=',l.product_id.id),('lot_id','=',l.lot_id.id),('location_id.usage','in',('customer','supplier'))])
			for n in otro:
				if n.quantity >0:
					self.env['kardex.vs.quant.view'].create({
						'motivo':'Serie Duplicado',
						'product_id':i.product_id.id,
						'lot_id':i.lot_id.id,
						'location_id': i.location_id.id,
						'qty_odoo':i.quantity,
						'qty_reservado_odoo':i.reserved_quantity,
						'qty_kardex':0,
						'qty_reservado_kardex':0,
						})

		return {				
			'name': 'Kardex vs Quants Descuadre',
			'type': 'ir.actions.act_window',
			'res_model': 'kardex.vs.quant.view',
			'view_mode': 'tree',
			'views': [(False, 'tree')],
		}