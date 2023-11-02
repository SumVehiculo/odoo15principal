from odoo import models, fields, api
from odoo.addons.payment.models.payment_acquirer import ValidationError
from odoo.exceptions import UserError
import base64

class stock_picking(models.Model):
	_inherit = 'stock.picking'

	lotes_file = fields.Binary('Nro de Lotes',help="Archivo csv con el listado de series, separador requerido es |")
	errores_txt = fields.Text("Errores de Importación Lotes")
	tipo_import_lot = fields.Selection([('name','Nombre Producto'),('default_code','Codigo Interno Producto')],u'Columna para Importación para Producto',default='name')
	remove_rest = fields.Boolean(u'Remover líneas que no están en el archivo a importar', default=True)



	def get_read_lotes(self):
		for l in self:
			if not self.lotes_file:
				raise UserError("Debe cargar un archivo de importación.")

			if self.picking_type_id.code == 'incoming':
				data = base64.b64decode(self.lotes_file).decode('utf-8')
				info = data.split('\n')
				cont = 0
				verificacion_lotes = []
				contenedor_lotes = {}
				errores = ""
				for i in info:
					data_linea = i.split('|')
					if len(data_linea)==5:
						if (data_linea[0].strip(),data_linea[1].strip()) in verificacion_lotes:
							if ("El nro de lote esta duplicado: (" + data_linea[0].strip() +"," +data_linea[1].strip() + ")\n")  in errores:
								pass
							else:
								errores += ("El nro de lote esta duplicado: (" + data_linea[0].strip() +"," +data_linea[1].strip() + ")\n")
						verificacion_lotes.append( (data_linea[0].strip(),data_linea[1].strip()) )                    

						producto = self.env['product.product'].search([(l.tipo_import_lot,'=',data_linea[0].strip())])
						if len(producto)>0:
							existe_lote = self.env['stock.production.lot'].search([('name','=',data_linea[1].strip()),('product_id.'+l.tipo_import_lot,'=',data_linea[0].strip())])
							if len(existe_lote)>0:
								errores += "Ya existe el lote para el producto seleccionado: (" + data_linea[0].strip()+ "," + data_linea[1].strip() + ")\n"
							key_imp = None
							if producto[0].tracking == 'lot':
								key_imp= (producto[0].id,data_linea[1].strip())
							if producto[0].tracking == 'serial':
								key_imp= (producto[0].id,'serie')
							if producto[0].tracking == 'none':
								key_imp= (producto[0].id,'none')
							if key_imp==None:
								errores += "El producto: " + data_linea[0].strip()  + "no tiene seguimiento por lotes o series\n"

							if key_imp in contenedor_lotes:
								detalle_lotes = contenedor_lotes[key_imp]
								detalle_lotes.append(data_linea)
								contenedor_lotes[key_imp] = detalle_lotes
							else:
								contenedor_lotes[key_imp] = [data_linea]
						else:
							if ("No existe el producto: " + data_linea[0].strip() + "\n" ) in errores:
								pass
							else:
								errores += "No existe el producto: " + data_linea[0].strip()  + "\n"
				self.errores_txt = errores

				#if errores !="":
				#	return

				if l.state == 'draft':                    

					for elem in contenedor_lotes:
						#C310|0E0VHV|67|01/18/2020|78.76
						data = {
							'product_id':elem,
							'product_uom_qty':len(contenedor_lotes[elem]) if self.env['product.product'].browse(elem[0]).tracking == 'serial' else float(contenedor_lotes[elem][0][2]),
							'name':self.env['product.product'].browse(elem[0]).name,
							'product_uom':self.env['product.product'].browse(elem[0]).uom_id.id,
							'location_id':self.location_id.id,
							'location_dest_id':self.location_dest_id.id,
							'picking_type_id':self.picking_type_id.id,
							'price_unit_it':float(contenedor_lotes[elem][0][4].strip()) if contenedor_lotes[elem][0][4].strip() != "" else 0,
						}
						self.write({'move_ids_without_package':[(0,0,data)]})                    
					l.action_confirm()

					for lineas_eliminanr in self.move_line_ids_without_package:
						if lineas_eliminanr.tracking == 'serial':
							lineas_eliminanr.unlink()
						elif lineas_eliminanr.tracking == 'lot':
							lineas_eliminanr.unlink()
						elif lineas_eliminanr.tracking == 'none':
							lineas_eliminanr.unlink()
					
					for i in self.move_ids_without_package:
						if i.product_id.tracking == 'serial':
							data = {
								'product_id':i.product_id.id,
								'move_id':i.id,
								'next_serial_count':i.product_uom_qty,
								'next_serial_number':1,
							}
							obj_tmp = self.env['stock.assign.serial'].create(data)
							obj_tmp.generate_serial_numbers()

					for elem in contenedor_lotes:
						#C310|0E0VHV|67|01/18/2020|78.76|
						if self.env['product.product'].browse(elem[0]).tracking == 'lot':
							elem_move_picking = None
							elem_move_pickingx = self.env['stock.move'].search([('picking_id','=',self.id),('product_id','=',elem[0]),('product_uom_qty','=',float(contenedor_lotes[elem][0][2]))])
							for e in elem_move_pickingx:
								conexion = self.env['stock.move.line'].search([('move_id','=',e.id)])
								if len(conexion) == 0:
									elem_move_picking = e
									
							if len(elem_move_picking)>1:
								raise UserError("dos stockmoves:" +str(elem_move_picking.product_id.default_code))
							move_line_vals = {
								'picking_id': self.id,
								'location_dest_id': self.location_dest_id.id,
								'location_id': self.location_id.id,
								'product_id': elem_move_picking.product_id.id,
								'product_uom_id': elem_move_picking.product_uom.id,
								'qty_done': float(contenedor_lotes[elem][0][2]),
								'package_level_id':False,
								'move_id':elem_move_picking.id,
							}
							self.env['stock.move.line'].create(move_line_vals)
						elif self.env['product.product'].browse(elem[0]).tracking == 'none':
							elem_move_picking = self.env['stock.move'].search([('picking_id','=',self.id),('product_id','=',elem[0])])
							if len(elem_move_picking)>1:
								raise UserError("dos stockmoves:" +str(elem_move_picking.product_id.default_code))
							move_line_vals = {
								'picking_id': self.id,
								'location_dest_id': self.location_dest_id.id,
								'location_id': self.location_id.id,
								'product_id': elem_move_picking.product_id.id,
								'product_uom_id': elem_move_picking.product_uom.id,
								'qty_done': float(contenedor_lotes[elem][0][2]),
								'package_level_id':False,
								'move_id':elem_move_picking.id,
							}
							self.env['stock.move.line'].create(move_line_vals)
				self.refresh()
				self.move_line_ids_without_package.refresh()
				for i in self.move_line_ids_without_package:
					i.lot_name = False
				for elem in contenedor_lotes:
					producto_obj = self.env['product.product'].browse(elem[0])
					if producto_obj.tracking == 'serial':
						lineas_por_actualizar = self.move_line_ids_without_package.filtered(lambda r: r.product_id.id == elem[0])
						if len(lineas_por_actualizar) == 0:
							raise UserError("No existe en el albaran el producto: " +  self.env['product.product'].browse(elem[0]).name)

						if len( lineas_por_actualizar ) >= len(contenedor_lotes[elem]) :
							cont = 0
							for actual_lot in contenedor_lotes[elem]:
								lineas_por_actualizar[cont].lot_name = actual_lot[1]
								lineas_por_actualizar[cont].qty_done = 1
								cont += 1
						else:
							raise UserError("El nro de lotes es mayor para el producto: " +  lineas_por_actualizar[0].product_id.name)
					elif producto_obj.tracking == 'lot':
						self.move_line_ids_without_package.refresh()						
						lineas_por_actualizar = self.move_line_ids_without_package.filtered(lambda r: r.product_id.id == elem[0] and not r.lot_name)
						if len(lineas_por_actualizar) == 0:
							raise UserError("No existe en el albaran el producto: " +  self.env['product.product'].browse(elem[0]).name)

						if len( lineas_por_actualizar ) >= len(contenedor_lotes[elem]) :
							cont = 0
							for actual_lot in contenedor_lotes[elem]:
								lineas_por_actualizar[cont].lot_name = actual_lot[1]
								lineas_por_actualizar[cont].qty_done = contenedor_lotes[elem][0][2]
								cont += 1
						else:
							raise UserError("El nro de lotes es mayor para el producto: " +  lineas_por_actualizar[0].product_id.name)

					elif producto_obj.tracking == 'none':
						self.move_line_ids_without_package.refresh()						
						lineas_por_actualizar = self.move_line_ids_without_package.filtered(lambda r: r.product_id.id == elem[0] and not r.lot_name)
						if len(lineas_por_actualizar) == 0:
							raise UserError("No existe en el albaran el producto: " +  self.env['product.product'].browse(elem[0]).name)
						if len( lineas_por_actualizar ) >= len(contenedor_lotes[elem]) :
							cont = 0
							for actual_lot in contenedor_lotes[elem]:
								lineas_por_actualizar[cont].qty_done = contenedor_lotes[elem][0][2]
								cont += 1
						else:
							raise UserError("El nro de lotes es mayor para el producto: " +  lineas_por_actualizar[0].product_id.name)
			else:
				data = base64.b64decode(self.lotes_file).decode('utf-8')
				info = data.split('\n')
				cont = 0
				verificacion_lotes = []
				contenedor_lotes = {}
				errores = ""
				for i in info:
					data_linea = i.split('|')
					if len(data_linea)==5:

						if data_linea[1].strip() in verificacion_lotes:
							if ("El nro de lote esta duplicado: " + data_linea[1].strip() + "\n")  in errores:
								pass
							else:
								errores += "El nro de lote esta duplicado: " + data_linea[1].strip() + "\n"
						verificacion_lotes.append(data_linea[1].strip())                    

						producto = self.env['product.product'].search([(l.tipo_import_lot,'=',data_linea[0].strip())])
						if len(producto)>0:

							existe_lote = self.env['stock.production.lot'].search([('name','=',data_linea[1].strip()),('product_id.'+l.tipo_import_lot,'=',data_linea[0].strip())])
							if len(existe_lote)==0:
								errores += "No existe el lote para el producto seleccionado: (" + data_linea[0].strip()+ "," + data_linea[1].strip() + ")\n"

							key_imp = None
							if producto[0].tracking == 'lot':
								key_imp= (producto[0].id,data_linea[1].strip())
							if producto[0].tracking == 'serial':
								key_imp= (producto[0].id,'serie')
							if producto[0].tracking == 'none':
								key_imp= (producto[0].id,'none')
							

							if key_imp in contenedor_lotes:
								detalle_lotes = contenedor_lotes[key_imp]
								detalle_lotes.append(data_linea)
								contenedor_lotes[key_imp] = detalle_lotes
							else:
								contenedor_lotes[key_imp] = [data_linea]
						else:
							if ("No existe el producto: " + data_linea[0].strip() + "\n" ) in errores:
								pass
							else:
								errores += "No existe el producto: " + data_linea[0].strip()  + "\n"
				self.errores_txt = errores				

				if errores != "":
					return
				lines_updated=[]

				for elem in contenedor_lotes:
					producto_obj = self.env['product.product'].browse(elem[0])
					if producto_obj.tracking == 'serial':
						lineas_por_actualizar = self.move_line_ids_without_package.filtered(lambda r: r.product_id.id == elem[0])
						if len(lineas_por_actualizar) == 0:
							raise UserError("No existe en el albaran el producto: " +  self.env['product.product'].browse(elem[0]).name)

						if len( lineas_por_actualizar ) >= len(contenedor_lotes[elem]) :
							cont = 0
							for actual_lot in contenedor_lotes[elem]:
								lineas_por_actualizar[cont].lot_id = self.env['stock.production.lot'].search([('name','=',actual_lot[1]),('product_id','=',elem[0])] ) 
								lineas_por_actualizar[cont].qty_done = 1
								lines_updated.append(lineas_por_actualizar[cont].id)
								cont += 1
						else:
							raise UserError("El nro de lotes es mayor para el producto: " +  lineas_por_actualizar[0].product_id.name)

					elif producto_obj.tracking == 'lot':
						self.move_line_ids_without_package.refresh()						
						lineas_por_actualizar = self.move_line_ids_without_package.filtered(lambda r: r.product_id.id == elem[0] and r.qty_done == contenedor_lotes[elem][0][2] and r.lot_id.id == False)
						if len(lineas_por_actualizar) == 0:
							raise UserError("No existe en el albaran el producto: " +  self.env['product.product'].browse(elem[0]).name)

						if len( lineas_por_actualizar ) >= len(contenedor_lotes[elem]) :
							cont = 0
							for actual_lot in contenedor_lotes[elem]:
								lineas_por_actualizar[cont].lot_id = self.env['stock.production.lot'].search([('name','=',actual_lot[1]),('product_id','=',elem[0])] ) 
								cont += 1
						else:
							raise UserError("El nro de lotes es mayor para el producto: " +  lineas_por_actualizar[0].product_id.name)
					elif producto_obj.tracking == 'none':
						self.move_line_ids_without_package.refresh()						
						lineas_por_actualizar = self.move_line_ids_without_package.filtered(lambda r: r.product_id.id == elem[0] and r.qty_done == contenedor_lotes[elem][0][2] and r.lot_id.id == False)
						if len(lineas_por_actualizar) == 0:
							raise UserError("No existe en el albaran el producto: " +  self.env['product.product'].browse(elem[0]).name)
						if len( lineas_por_actualizar ) >= len(contenedor_lotes[elem]) :
							cont = 0
							for actual_lot in contenedor_lotes[elem]:
								cont += 1
						else:
							raise UserError("El nro de lotes es mayor para el producto: " +  lineas_por_actualizar[0].product_id.name)

				if self.remove_rest:
					self.move_line_ids_without_package.filtered(lambda r: r.id not in lines_updated).unlink()






	def get_read_lotesy(self):
		for l in self:
			if not self.lotes_file:
				raise UserError("Debe cargar un archivo de importación.")

			if self.picking_type_id.code == 'incoming':
				data = base64.b64decode(self.lotes_file).decode('utf-8')
				info = data.split('\n')
				cont = 0
				verificacion_lotes = []
				contenedor_lotes = {}
				errores = ""
				for i in info:
					data_linea = i.split('|')
					if len(data_linea)==5:
						if (data_linea[0].strip(),data_linea[1].strip()) in verificacion_lotes:
							if ("El nro de lote esta duplicado: (" + data_linea[0].strip() +"," +data_linea[1].strip() + ")\n")  in errores:
								pass
							else:
								errores += ("El nro de lote esta duplicado: (" + data_linea[0].strip() +"," +data_linea[1].strip() + ")\n")
						verificacion_lotes.append( (data_linea[0].strip(),data_linea[1].strip()) )                    

						producto = self.env['product.product'].search([(l.tipo_import_lot,'=',data_linea[0].strip())])
						if len(producto)>0:
							key_imp = None
							if producto[0].tracking == 'lot':
								key_imp= (producto[0].id,data_linea[1].strip())
							if producto[0].tracking == 'serial':
								key_imp= (producto[0].id,'serie')

							if key_imp in contenedor_lotes:
								detalle_lotes = contenedor_lotes[key_imp]
								detalle_lotes.append(data_linea)
								contenedor_lotes[key_imp] = detalle_lotes
							else:
								contenedor_lotes[key_imp] = [data_linea]
						else:
							if ("No existe el producto: " + data_linea[0].strip() + "\n" ) in errores:
								pass
							else:
								errores += "No existe el producto: " + data_linea[0].strip()  + "\n"
				self.errores_txt = errores


				if l.state == 'draft':                    

					for elem in contenedor_lotes:
						#C310|0E0VHV|67|01/18/2020|78.76|
						data = {
							'product_id':elem,
							'product_uom_qty':len(contenedor_lotes[elem]) if self.env['product.product'].browse(elem[0]).tracking == 'serial' else float(contenedor_lotes[elem][0][2]),
							'name':self.env['product.product'].browse(elem[0]).name,
							'product_uom':self.env['product.product'].browse(elem[0]).uom_id.id,
							'location_id':self.location_id.id,
							'location_dest_id':self.location_dest_id.id,
							'picking_type_id':self.picking_type_id.id,
							'price_unit_it':float(contenedor_lotes[elem][0][4]),
						}
						self.write({'move_ids_without_package':[(0,0,data)]})                    
					l.action_confirm()

					for lineas_eliminanr in self.move_line_ids_without_package:
						if lineas_eliminanr.tracking == 'serial':
							lineas_eliminanr.unlink()
						elif lineas_eliminanr.tracking == 'lot':
							lineas_eliminanr.unlink()
					
					for i in self.move_ids_without_package:
						if i.product_id.tracking == 'serial':
							data = {
								'product_id':i.product_id.id,
								'move_id':i.id,
								'next_serial_count':i.product_uom_qty,
								'next_serial_number':1,
							}
							obj_tmp = self.env['stock.assign.serial'].create(data)
							obj_tmp.generate_serial_numbers()

					for elem in contenedor_lotes:
						#C310|0E0VHV|67|01/18/2020|78.76|
						if self.env['product.product'].browse(elem[0]).tracking == 'lot':
							elem_move_picking = self.env['stock.move'].search([('picking_id','=',self.id),('product_id','=',elem[0])])
							if len(elem_move_picking)>1:
								raise UserError("dos stockmoves:" +str(elem_move_picking.product_id.default_code))
							move_line_vals = {
								'picking_id': self.id,
								'location_dest_id': self.location_dest_id.id,
								'location_id': self.location_id.id,
								'product_id': elem_move_picking.product_id.id,
								'product_uom_id': elem_move_picking.product_uom.id,
								'qty_done': float(contenedor_lotes[elem][0][2]),
								'package_level_id':False,
								'move_id':elem_move_picking.id,
							}
							self.env['stock.move.line'].create(move_line_vals)
				
				self.refresh()
				self.move_line_ids_without_package.refresh()
				for elem in contenedor_lotes:
					producto_obj = self.env['product.product'].browse(elem[0])
					if producto_obj.tracking == 'serial':
						lineas_por_actualizar = self.move_line_ids_without_package.filtered(lambda r: r.product_id.id == elem[0])
						if len(lineas_por_actualizar) == 0:
							raise UserError("No existe en el albaran el producto: " +  self.env['product.product'].browse(elem[0]).name)

						if len( lineas_por_actualizar ) >= len(contenedor_lotes[elem]) :
							cont = 0
							for actual_lot in contenedor_lotes[elem]:
								lineas_por_actualizar[cont].lot_id = self.env['stock.production.lot'].create({'name':actual_lot[1],'product_id': elem[0],'company_id':self.env.company.id }) 
								lineas_por_actualizar[cont].qty_done = 1
								cont += 1
						else:
							raise UserError("El nro de lotes es mayor para el producto: " +  lineas_por_actualizar[0].product_id.name)
					if producto_obj.tracking == 'lot':
						self.move_line_ids_without_package.refresh()						
						lineas_por_actualizar = self.move_line_ids_without_package.filtered(lambda r: r.product_id.id == elem[0] and r.lot_id.id == False)
						if len(lineas_por_actualizar) == 0:
							raise UserError("No existe en el albaran el producto: " +  self.env['product.product'].browse(elem[0]).name)

						if len( lineas_por_actualizar ) >= len(contenedor_lotes[elem]) :
							cont = 0
							for actual_lot in contenedor_lotes[elem]:
								lineas_por_actualizar[cont].lot_id = self.env['stock.production.lot'].create({'name':actual_lot[1],'product_id': elem[0],'company_id':self.env.company.id  }) 
								lineas_por_actualizar[cont].qty_done = contenedor_lotes[elem][0][2]
								cont += 1
						else:
							raise UserError("El nro de lotes es mayor para el producto: " +  lineas_por_actualizar[0].product_id.name)

			else:
				data = base64.b64decode(self.lotes_file).decode('utf-8')
				info = data.split('\n')
				cont = 0
				verificacion_lotes = []
				contenedor_lotes = {}
				errores = ""
				for i in info:
					data_linea = i.split('|')
					if len(data_linea)==5:

						if data_linea[1].strip() in verificacion_lotes:
							if ("El nro de lote esta duplicado: " + data_linea[1].strip() + "\n")  in errores:
								pass
							else:
								errores += "El nro de lote esta duplicado: " + data_linea[1].strip() + "\n"
						verificacion_lotes.append(data_linea[1].strip())                    

						producto = self.env['product.product'].search([(l.tipo_import_lot,'=',data_linea[0].strip())])
						if len(producto)>0:
							key_imp = None
							if producto[0].tracking == 'lot':
								key_imp= (producto[0].id,data_linea[1].strip())
							if producto[0].tracking == 'serial':
								key_imp= (producto[0].id,'serie')

							if key_imp in contenedor_lotes:
								detalle_lotes = contenedor_lotes[key_imp]
								detalle_lotes.append(data_linea)
								contenedor_lotes[key_imp] = detalle_lotes
							else:
								contenedor_lotes[key_imp] = [data_linea]
						else:
							if ("No existe el producto: " + data_linea[0].strip() + "\n" ) in errores:
								pass
							else:
								errores += "No existe el producto: " + data_linea[0].strip()  + "\n"
				self.errores_txt = errores				


				for elem in contenedor_lotes:

					producto_obj = self.env['product.product'].browse(elem[0])
					if producto_obj.tracking == 'serial':
						lineas_por_actualizar = self.move_line_ids_without_package.filtered(lambda r: r.product_id.id == elem[0])
						if len(lineas_por_actualizar) == 0:
							raise UserError("No existe en el albaran el producto: " +  self.env['product.product'].browse(elem[0]).name)

						if len( lineas_por_actualizar ) >= len(contenedor_lotes[elem]) :
							cont = 0
							for actual_lot in contenedor_lotes[elem]:
								lineas_por_actualizar[cont].lot_id = self.env['stock.production.lot'].search([('name','=',actual_lot[1]),('product_id','=',elem[0])] ) 
								lineas_por_actualizar[cont].qty_done = 1
								cont += 1
						else:
							raise UserError("El nro de lotes es mayor para el producto: " +  lineas_por_actualizar[0].product_id.name)
					if producto_obj.tracking == 'lot':
						self.move_line_ids_without_package.refresh()						
						lineas_por_actualizar = self.move_line_ids_without_package.filtered(lambda r: r.product_id.id == elem[0] and r.qty_done == contenedor_lotes[elem][0][2] and r.lot_id.id == False)
						if len(lineas_por_actualizar) == 0:
							raise UserError("No existe en el albaran el producto: " +  self.env['product.product'].browse(elem[0]).name)

						if len( lineas_por_actualizar ) >= len(contenedor_lotes[elem]) :
							cont = 0
							for actual_lot in contenedor_lotes[elem]:
								lineas_por_actualizar[cont].lot_id = self.env['stock.production.lot'].search([('name','=',actual_lot[1]),('product_id','=',elem[0])] ) 
								cont += 1
						else:
							raise UserError("El nro de lotes es mayor para el producto: " +  lineas_por_actualizar[0].product_id.name)





	def get_read_lotesx(self):
		for l in self:
			if not self.lotes_file:
				raise UserError("Debe cargar un archivo de importación.")

			if self.picking_type_id.code == 'incoming':
				data = base64.b64decode(self.lotes_file).decode('utf-8')
				info = data.split('\n')
				cont = 0
				verificacion_lotes = []
				contenedor_lotes = {}
				errores = ""
				for i in info:
					data_linea = i.split('|')
					if len(data_linea)==2:
						if data_linea[1].strip() in verificacion_lotes:
							if ("El nro de lote esta duplicado: " + data_linea[1].strip() + "\n")  in errores:
								pass
							else:
								errores += "El nro de lote esta duplicado: " + data_linea[1].strip() + "\n"
						verificacion_lotes.append(data_linea[1].strip())                    

						producto = self.env['product.product'].search([(l.tipo_import_lot,'=',data_linea[0].strip())])
						if len(producto)>0:
							if producto[0].id in contenedor_lotes:
								detalle_lotes = contenedor_lotes[producto[0].id]
								detalle_lotes.append(data_linea[1].strip())
								contenedor_lotes[producto[0].id] = detalle_lotes
							else:
								contenedor_lotes[producto[0].id] = [data_linea[1].strip()]
						else:
							if ("No existe el producto: " + data_linea[0].strip() + "\n" ) in errores:
								pass
							else:
								errores += "No existe el producto: " + data_linea[0].strip()  + "\n"
				self.errores_txt = errores
				#if errores != "":
				#	raise UserError(errores)

				if l.state == 'draft':                    

					for elem in contenedor_lotes:
						data = {
							'product_id':elem,
							'product_uom_qty':len(contenedor_lotes[elem]),
							'name':self.env['product.product'].browse(elem).name,
							'product_uom':self.env['product.product'].browse(elem).uom_id.id,
							'location_id':self.location_id.id,
							'location_dest_id':self.location_dest_id.id,
							'picking_type_id':self.picking_type_id.id,
						}
						self.write({'move_ids_without_package':[(0,0,data)]})                    
					l.action_confirm()
					self.move_line_ids_without_package.unlink()
					for i in self.move_ids_without_package:
						data = {
							'product_id':i.product_id.id,
							'move_id':i.id,
							'next_serial_count':i.product_uom_qty,
							'next_serial_number':1,
						}
						obj_tmp = self.env['stock.assign.serial'].create(data)
						obj_tmp.generate_serial_numbers()
				
				self.refresh()
				self.move_line_ids_without_package.refresh()
				for elem in contenedor_lotes:
					lineas_por_actualizar = self.move_line_ids_without_package.filtered(lambda r: r.product_id.id == elem)
					if len(lineas_por_actualizar) == 0:
						raise UserError("No existe en el albaran el producto: " +  self.env['product.product'].browse(elem).name)

					if len( lineas_por_actualizar ) >= len(contenedor_lotes[elem]) :
						cont = 0
						for actual_lot in contenedor_lotes[elem]:
							lineas_por_actualizar[cont].lot_name = actual_lot
							lineas_por_actualizar[cont].qty_done = 1
							cont += 1
					else:
						raise UserError("El nro de lotes es mayor para el producto: " +  lineas_por_actualizar[0].product_id.name)

			else:
				data = base64.b64decode(self.lotes_file).decode('utf-8')
				info = data.split('\n')
				cont = 0
				verificacion_lotes = []
				contenedor_lotes = {}
				for i in info:
					data_linea = i.split('|')
					if len(data_linea)==2:
						if data_linea[1].strip() in verificacion_lotes:
							raise UserError("El nro de lote esta duplicado: " + data_linea[1].strip())
						verificacion_lotes.append(data_linea[1].strip())                    

						producto = self.env['product.product'].search([(l.tipo_import_lot,'=',data_linea[0].strip())])
						if len(producto)>0:
							if producto[0].id in contenedor_lotes:
								detalle_lotes = contenedor_lotes[producto[0].id]
								detalle_lotes.append(data_linea[1].strip())
								contenedor_lotes[producto[0].id] = detalle_lotes
							else:
								contenedor_lotes[producto[0].id] = [data_linea[1].strip()]
						else:
							raise UserError("No existe el producto: " + data_linea[0].strip() )

				for elem in contenedor_lotes:
					lineas_por_actualizar = self.move_line_ids_without_package.filtered(lambda r: r.product_id.id == elem)
					if len(lineas_por_actualizar) == 0:
						raise UserError("No existe en el albaran el producto: " +  self.env['product.product'].browse(elem).name)

					if len( lineas_por_actualizar ) >= len(contenedor_lotes[elem]) :
						cont = 0
						for actual_lot in contenedor_lotes[elem]:
							lote_real =self.env['stock.production.lot'].search([('name','=',actual_lot)])
							if len(lote_real)>0:
								pass
							else:
								raise UserError("El nro de lotes no existe: " +  actual_lot)
							lineas_por_actualizar[cont].lot_id = self.env['stock.production.lot'].search([('name','=',actual_lot)])[0].id 
							lineas_por_actualizar[cont].qty_done = 1
							cont += 1
					else:
						raise UserError("El nro de lotes es mayor para el producto: " +  lineas_por_actualizar[0].product_id.name)

