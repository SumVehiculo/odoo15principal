# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta

class kardex_save_period_error(models.Model):
	_name = 'kardex.save.period.error'
	_description = "kardex save period error"

	save_id = fields.Many2one('kardex.save','Guardado Kardex')
	almacen = fields.Char(string='Tipo Ubicacion-origen')
	almacen_dest = fields.Char(string='Tipo Ubicacion-Destino')
	sunat = fields.Char(string='Codigo Sunat Error')
	sunat_esperado = fields.Char(string="Codigo Sunat Correcto")
	producto = fields.Many2one('product.product','Producto')
	code = fields.Char(related='producto.default_code')
	
	lote = fields.Many2one('stock.production.lot','Lote')
	
	picking_id = fields.Many2one("stock.picking",string="Albaran")



class kardex_save_period(models.Model):
	_name = 'kardex.save.period'
	_description = "kardex save period"

	save_id = fields.Many2one('kardex.save','Guardado Kardex')
	save_bad_id = fields.Many2one('kardex.save','Guardado Kardex')
	save_costo_bad_id = fields.Many2one('kardex.save','Guardado Kardex')
	save_costo_bad_id_dolar = fields.Many2one('kardex.save','Guardado Kardex')

	almacen = fields.Many2one('stock.location','Almacen')
	producto = fields.Many2one('product.product','Producto')
	categoria = fields.Many2one(related='producto.categ_id',string="Categoria del Producto")
	code = fields.Char(related='producto.default_code', string="Referencia Interna")
	unidad = fields.Many2one(related='producto.uom_id',string="UDM")
	fecha = fields.Date('Fecha')
	stock = fields.Float('Stock')
	lote = fields.Many2one('stock.production.lot','Lote')
	cprom = fields.Float('Costo Promedio',digits=(12,7))
	cprom_dolar = fields.Float('Costo Promedio Dolar',digits=(12,7))

class kardex_parameter_anios(models.Model):
	_name = 'kardex.parameter.anios'
	_description = "kardex parameter anios"

	kardex_id = fields.Many2one('kardex.parameter','Kardex Parameter')
	name = fields.Integer('Año')

	_order = 'name'

class kardex_parameter(models.Model):
	_name = 'kardex.parameter'
	_description = "kardex parameter"

	anio_ids = fields.One2many('kardex.parameter.anios','kardex_id',help=u"Años con Saldo Inicial")
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)

	picking_type_salida = fields.Many2one('stock.picking.type',string=u'Tipo Operacion Salida')
	picking_type_ingreso = fields.Many2one('stock.picking.type',string=u'Tipo Operacion Ingreso')

	def _get_anio_start(self,año_consulta):
		anio = 2000
		for i in self.anio_ids:
			if i.name<= año_consulta:
				if i.name > anio:
					anio = i.name
		return anio

class stock_picking(models.Model):
	_inherit = 'stock.picking'

	save_id = fields.Many2one('kardex.save','Guardado')

class KardexSave(models.Model):
	_name = 'kardex.save'
	_description = "kardex save"
	_inherit = 'mail.thread'

	name = fields.Many2one('account.period.kardex',string='Periodo')
	state = fields.Selection([('draft', 'Borrador'),('first','Fisico OK'),('valorized','Valorización'),('val_sol','Valorización Soles OK'),('valorized_dol','Valorización Dolares'),('val_dol','Valorización Dolares OK'), ('done', 'Finalizado')],string='Estado', default='draft', tracking=True)
	date = fields.Datetime('Fecha Guardado', tracking=True)
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	color = fields.Integer('Color',compute="get_color")
	lineas = fields.One2many('kardex.save.period','save_id','Detalle')
	lineas_cero = fields.One2many('kardex.save.period','save_bad_id','Negativos')
	lineas_cero_cero = fields.One2many('kardex.save.period','save_costo_bad_id','Costo cero')
	lineas_cero_cero_dolar = fields.One2many('kardex.save.period','save_costo_bad_id_dolar','Costo cero Dolar')


	lineas_mal = fields.One2many('kardex.save.period.error','save_id','Sugerencia OP. SUNAT')
	albaranes = fields.One2many('stock.picking','save_id','Albaranes')
	albaranes_count = fields.Integer('# Albaranes',compute="get_albaranes_count")
	fecha_creacion = fields.Datetime(string="Fecha de Creación", tracking=True)
	fecha_finalizado = fields.Datetime(string="Fecha Finalizado", tracking=True)

	tienelineas_cero_cero = fields.Boolean(string="Tiene Costos Cero",compute="get_csto_cero_view")
	tienelineas_cero_cero_dolar = fields.Boolean(string="Tiene Costos Cero Dolar",compute="get_csto_cero_view")
	tienelineas_cero = fields.Boolean(string="Tiene Costos Cero",compute="get_csto_cero_view")

	check_procecenvalorizado_once = fields.Boolean(string="Permitir Aprobar costo Cero",default=False,copy=False)
	corriovalorizado = fields.Boolean(string="Permitir Aprobar costo Cero Dolar",default=False,copy=False)

	@api.depends("name","lineas_cero","lineas_cero_cero","lineas_cero_cero_dolar")
	def get_csto_cero_view(self):
		for i in self:
			i.tienelineas_cero_cero = True if len(i.lineas_cero_cero)!=0 else False
			i.tienelineas_cero = True if len(i.lineas_cero)!=0 else False
			i.tienelineas_cero_cero_dolar = True if len(i.lineas_cero_cero_dolar)!=0 else False



	fecha_aprob_costo_cero = fields.Datetime(string="Fecha Aprobación", copy=False)
	user_aprob_costo_cero_id = fields.Many2one("res.users",string="Usuario Aprobación",copy=False, help="Permite aprobar las operaciones del kardex cuyo costo es 0(Zero).")

	fecha_aprob_costo_cero_dolar = fields.Datetime(string="Fecha Aprobación", copy=False)
	user_aprob_costo_cero_id_dolar = fields.Many2one("res.users",string="Usuario Aprobación",copy=False, help="Permite aprobar las operaciones del kardex cuyo costo Dolar es 0(Zero).")

	fecha_aprob_sunat_oper = fields.Datetime(string="Fecha Aprobación", copy=False)
	user_aprob_sunat_oper = fields.Many2one("res.users",string="Usuario Aprobación",copy=False,help="Permite aprobar el detalle de tipos de operación Sunat no conformes.")

	date_start_related = fields.Date(string="Inicio",related="name.date_start",store=True)
	date_fin_related = fields.Date(string="Fin",related="name.date_end",store=True)






	_order = 'name'

	def get_albaranes_count(self):
		for i in self:
			i.albaranes_count = len(i.albaranes)

	def get_albaranes_list(self):
		return {
			'name': 'Albaranes',
			'type': 'ir.actions.act_window',
			'res_model': 'stock.picking',
			'view_mode': 'tree,form',
			'domain': [('save_id','=',self.id)],
		}

	def eliminar_saldos(self):
		for i in self:
			for l in i.albaranes:
				if l.state == 'draft':
					self.env.cr.execute(""" delete from stock_move_line where picking_id = """+ str(l.id) )
					self.env.cr.execute(""" delete from stock_move where picking_id = """+ str(l.id) )
					self.env.cr.execute(""" delete from stock_picking where id = """+ str(l.id) )


	def anular_saldos(self):
		for i in self:
			for l in i.albaranes:
				if l.state == 'done':
					l.origin="ANULADO"
					for elem in l.move_line_ids_without_package:
						elem.qty_done = 0

	def crear_saldos(self):		

		text_report = "<b>Generando Albaranes para Saldos del Nuevo Año</b>"
		self.send_message(text_report)


		config = self.env['kardex.parameter'].search([('company_id','=',self.env.company.id)])
		for i in self:
			if not config.picking_type_ingreso.id or not config.picking_type_salida.id:
				raise UserError("No se configuro los tipo de operaciones")

			fecha_ingreso = str(i.name.date_end + timedelta(days=1)) + ' 05:00:00'
			fecha_salida = str(i.name.date_end + timedelta(days=1)) + ' 04:59:59'
			tiempo_inicial = datetime.now()
			cont_report  =0
			for l in i.lineas:
				if l.stock >0:

					cont_report += 1
					if cont_report%100 == 0:
						tiempo_pasado = divmod((datetime.now()-tiempo_inicial).seconds,60)
						text_report = ""
						text_report = "<b>Generando Albaranes para Saldos del Nuevo Año</b><br/><center>Total lineas a procesar: "+str(len(i.lineas)) + "</center><br/><center>Procesado:"+str(cont_report)+"/"+str(len(i.lineas))+"</center><br/> Tiempo Procesado: "+ str(tiempo_pasado[0])+" minutos " +str(tiempo_pasado[1]) + " segundos" 
						text_report += """<div id="myProgress" style="position: relative; width: 100%;  height: 30px;   background-color: white;">
						  <div id="myBar" style="position: absolute;  width: """+"%.2f"%(cont_report*100/len(i.lineas))+"""%;  height: 100%; background-color: #875A7B;">
						    <div id="label" style="text-align: center; line-height: 30px; color: white;">""" +"%.2f"%(cont_report*100/len(i.lineas))+ """%</div>
						  </div>
						</div>"""
						self.send_message(text_report)

					alb_salida = i.albaranes.search([('location_id','=',l.almacen.id),('save_id','=',i.id),('state','=','draft')])
					if len(alb_salida) == 0:
						data = {
							'save_id':i.id,
							'kardex_date':fecha_salida,
							'picking_type_id':config.picking_type_salida.id,
							'location_id':l.almacen.id,
							'location_dest_id':config.picking_type_salida.default_location_dest_id.id,
							'company_id':i.company_id.id,
						}
						alb_salida = self.env['stock.picking'].create(data)


					alb_ingreso = i.albaranes.search([('location_dest_id','=',l.almacen.id),('save_id','=',i.id),('state','=','draft')])
					if len(alb_ingreso) == 0:
						data = {
							'save_id':i.id,
							'kardex_date':fecha_ingreso,
							'picking_type_id':config.picking_type_ingreso.id,
							'location_id':config.picking_type_ingreso.default_location_src_id.id,
							'location_dest_id': l.almacen.id,
							'company_id':i.company_id.id,
						}
						alb_ingreso = self.env['stock.picking'].create(data)						

					self.env.cr.execute(""" INSERT INTO STOCK_MOVE(name,product_id,product_qty,product_uom_qty, price_unit_it, product_uom,picking_id,picking_type_id, location_id,location_dest_id,company_id,date,date_expected,procure_method,state)
						values ('"""+l.producto.name_get()[0][1]+"""',
							"""+str(l.producto.id)+""",
							"""+str(l.stock)+""",
							"""+str(l.stock)+""",
							"""+str(l.cprom)+""",
							"""+str(l.producto.uom_id.id)+""",
							"""+str(alb_salida.id)+""",
							"""+str(alb_salida.picking_type_id.id)+""",
							"""+str(alb_salida.location_id.id)+""",
							"""+str(alb_salida.location_dest_id.id)+""",
							"""+str(i.company_id.id)+""",
							'"""+str(fecha_salida)+"""'::date,
							'"""+str(fecha_salida)+"""'::date,
							'make_to_stock',
							'confirmed') RETURNING id
					 """)

					id_linea_salida = self.env.cr.fetchall()[0][0]


					self.env.cr.execute(""" INSERT INTO STOCK_MOVE_LINE(move_id,lot_id,product_id,qty_done,product_uom_qty,product_uom_id,picking_id,location_id,location_dest_id,company_id,date,state)
						values ("""+str(id_linea_salida)+""",
						"""+str(str(l.lote.id) if l.lote.id else 'NULL')+""",
							"""+str(l.producto.id)+""",
							"""+str(0)+""",
							"""+str(0)+""",
							"""+str(l.producto.uom_id.id)+""",
							"""+str(alb_salida.id)+""",
							"""+str(alb_salida.location_id.id)+""",
							"""+str(alb_salida.location_dest_id.id)+""",
							"""+str(i.company_id.id)+""",
							'"""+str(fecha_salida)+"""'::date,
							'confirmed') RETURNING id
					 """)

					self.env.cr.execute(""" INSERT INTO STOCK_MOVE(name,product_id,product_qty,product_uom_qty, price_unit_it, product_uom,picking_id,picking_type_id, location_id,location_dest_id,company_id,date,date_expected,procure_method,state)
						values ('"""+l.producto.name_get()[0][1]+"""',
							"""+str(l.producto.id)+""",
							"""+str(l.stock)+""",
							"""+str(l.stock)+""",
							"""+str(l.cprom)+""",
							"""+str(l.producto.uom_id.id)+""",
							"""+str(alb_ingreso.id)+""",
							"""+str(alb_ingreso.picking_type_id.id)+""",
							"""+str(alb_ingreso.location_id.id)+""",
							"""+str(alb_ingreso.location_dest_id.id)+""",
							"""+str(i.company_id.id)+""",
							'"""+str(fecha_ingreso)+"""'::date,
							'"""+str(fecha_ingreso)+"""'::date,
							'make_to_stock',
							'confirmed') RETURNING id
					 """)

					id_linea_ingreso = self.env.cr.fetchall()[0][0]

					self.env.cr.execute(""" INSERT INTO STOCK_MOVE_LINE(move_id,lot_id,product_id,qty_done,product_uom_qty,  product_uom_id,picking_id,location_id,location_dest_id,company_id,date,state)
						values ("""+str(id_linea_ingreso)+""",
						"""+str(str(l.lote.id) if l.lote.id else 'NULL')+""",
							"""+str(l.producto.id)+""",
							"""+str(0)+""",
							"""+str(0)+""",
							"""+str(l.producto.uom_id.id)+""",
							"""+str(alb_ingreso.id)+""",
							"""+str(alb_ingreso.location_id.id)+""",
							"""+str(alb_ingreso.location_dest_id.id)+""",
							"""+str(i.company_id.id)+""",
							'"""+str(fecha_ingreso)+"""'::date,
							'confirmed') RETURNING id
					 """)

			self.env.cr.execute(""" update stock_picking set state = 'confirmed' where state='draft' and  save_id = """+str(i.id))
					#dataline = {
					#	'name':l.producto.name_get()[0][1],
					#	'product_id':l.producto.id,
					#	'product_uom_qty':l.stock,
					#	'price_unit_it':l.cprom,
					#	'product_uom':l.producto.uom_id.id,
					#	'picking_id':alb_salida.id,
					#	'picking_type_id':alb_salida.picking_type_id.id,
					#	'location_id':alb_salida.location_id.id,
					#	'location_dest_id':alb_salida.location_dest_id.id,
					#	'company_id':i.company_id.id,
					#}
					#lineas = self.env['stock.move'].create(dataline)


					#dataline = {
					#	'name':l.producto.name_get()[0][1],
					#	'product_id':l.producto.id,
					#	'product_uom_qty':l.stock,
					#	'price_unit_it':l.cprom,
					#	'product_uom':l.producto.uom_id.id,
					#	'picking_id':alb_ingreso.id,
					#	'picking_type_id':alb_ingreso.picking_type_id.id,
					#	'location_id':alb_ingreso.location_id.id,
					#	'location_dest_id':alb_ingreso.location_dest_id.id,
					#	'company_id':i.company_id.id,
					#}
					#lineas = self.env['stock.move'].create(dataline)




	def get_color(self):
		for i in self:
			if i.state == 'draft':
				i.color = 1
			else:
				i.color = 10


	def unlink(self):
		for i in self:
			if i.state == 'draft':
				super(KardexSave,self).unlink()
			else:
				raise UserError('No se puede eliminar en estado Almacenado.')

	@api.constrains('name')
	def _verify_period(selfs):
		for self in selfs:
			if len(self.env['kardex.save'].search([('name','=',self.name.id)],limit=2)) > 1:
				raise UserError('No pueden existir dos guardados del mismo periodo')




	def save_valorado(self):
		cad = ""
		self.check_procecenvalorizado_once = True
		lineas_mal_delete = self.env["kardex.save.period"].sudo().search([("save_costo_bad_id","=",self.id)])
		lineas_mal_delete.sudo().unlink()
#		lineas_mal_delete = self.env["kardex.save.period"].sudo().search([("save_bad_id","=",self.id),("cprom","<=",0),("stock",">=",0)])
#		lineas_mal_delete.sudo().unlink()
#si se vuela las lineas antiguas no hay forma de asegurar que valorizaron el mes
		s_prod = [-1,-1,-1]
		s_loca = [-1,-1,-1]
		locat_ids = self.env['stock.location'].search( [('usage','in',('internal','inventory','transit','procurement','production'))] )
		lst_locations = locat_ids.ids
		
		productos='('
		almacenes='('

		lst_products = self.env['product.product'].with_context(active_test=False).search([]).ids

		
		if len(lst_products) == 0:
			raise UserError('No existen productos seleccionados')

		for producto in lst_products:
			productos=productos+str(producto)+','
			s_prod.append(producto)
		productos=productos[:-1]+')'
		for location in lst_locations:
			almacenes=almacenes+str(location)+','
			s_loca.append(location)
		almacenes=almacenes[:-1]+')'


		config = self.env['kardex.parameter'].search([('company_id','=',self.env.company.id)])

		date_fin = self.name.date_end
		date_ini = '%d-01-01' % ( config._get_anio_start(date_fin.year) )


		kardex_save_obj = self.env['kardex.save'].search([('company_id','=',self.env.company.id),('state','=','done'),('name.date_end','<',date_fin)]).sorted(lambda l: l.name.code , reverse=True)
		if len(kardex_save_obj)>0:
			kardex_save_obj = kardex_save_obj[0]
			date_ini = kardex_save_obj.name.date_end + timedelta(days=1)
		
		text_report_linea = ''
		if kardex_save_obj:
			text_report_linea = "<b>Se usara el saldo guardado: "+str(kardex_save_obj.name.code)+ " </b>"
			

		si_existe = ""
		if kardex_save_obj:
			si_existe = """union all


select 
				ksp.producto as product_id,
				ksp.almacen as location_id,
				'' as origen_usage,
				sl.usage as destino_usage,
				ksp.cprom * ksp.stock as debit,
				0 as credit,
				(fecha || ' 00:00:00')::timestamp as fechax,
				'' as type_doc,
				'' as serial,
				'' as nro,
				'' as numdoc_cuadre,
				'' as nro_documento,
				'Saldo Inicial' as name,
				'' as operation_type,
				pname.new_name,
				coalesce(pp.default_code,pt.default_code) as default_code,
				uu.name as unidad,
				ksp.stock as ingreso,
				0 as salida,
				ksp.cprom as cadquiere,
				'' as origen,
				sl.complete_name as destino,
				sl.complete_name as almacen

			from kardex_save_period ksp 
			inner join stock_location sl on sl.id = ksp.almacen
			inner join product_product pp on pp.id = ksp.producto
			inner join product_template pt on pt.id = pp.product_tmpl_id
			inner join uom_uom uu on uu.id = pt.uom_id
			inner join product_category pc on pc.id = pt.categ_id
			left join stock_production_lot spt on spt.id = ksp.lote
			 LEFT JOIN ( SELECT t_pp.id,
					((     coalesce(max(it.value),max(t_pt.name::text))::character varying::text || ' '::text) || replace(array_agg(pav.name)::character varying::text, '{NULL}'::text, ''::text))::character varying AS new_name
				   FROM product_product t_pp
					 JOIN product_template t_pt ON t_pp.product_tmpl_id = t_pt.id
					 left join ir_translation it ON t_pt.id = it.res_id and it.name = 'product.template,name' and it.lang = 'es_PE' and it.state = 'translated'
					 LEFT JOIN product_variant_combination pvc ON pvc.product_product_id = t_pp.id
					 LEFT JOIN product_template_attribute_value ptav ON ptav.id = pvc.product_template_attribute_value_id
					 LEFT JOIN product_attribute_value pav ON pav.id = ptav.product_attribute_value_id
				  GROUP BY t_pp.id) pname ON pname.id = pp.id
			 where save_id = """+str(kardex_save_obj.id)+"""
			 """

		text_report = "<b>Cargando Saldos Valorados</b><br/><center>Ejecutando SQL del kardex ... Espere por favor</center><br/>" + text_report_linea
		self.send_message(text_report)

		total_all = []


			

		self.env.cr.execute("""  
				select  
				product_id,
				location_id,
				origen_usage,
				destino_usage,
				debit,
				credit,
				fechax,
				type_doc,
				serial,
				nro,
				numdoc_cuadre,
				nro_documento,
				name,
				operation_type,
				new_name,
				default_code,
				unidad,
				ingreso,
				salida,
				cadquiere,
				origen,
				destino,
				almacen
		 from (
				select 
				product_id,
				location_id,
				origen_usage,
				destino_usage,
				debit,
				credit,
				fechax,
				type_doc,
				serial,
				nro,
				numdoc_cuadre,
				nro_documento,
				name,
				operation_type,
				new_name,
				default_code,
				unidad,
				ingreso,
				salida,
				cadquiere,
				origen,
				destino,
				almacen
				from (
	select vst_kardex_sunat.*,sp.name as doc_almac,sm.kardex_date as fecha_albaran,
	vst_kardex_sunat.fecha - interval '5' hour as fechax,sl_o.usage as origen_usage , sl_d.usage as destino_usage, np.new_name
				from vst_kardex_fisico_valorado as vst_kardex_sunat
	left join stock_move sm on sm.id = vst_kardex_sunat.stock_moveid
	left join stock_picking sp on sp.id = sm.picking_id

						left join stock_location sl_o on sl_o.id = sm.location_id
						left join stock_location sl_d on sl_d.id = sm.location_dest_id
	left join (
		select t_pp.id, 
	            ((     coalesce(max(it.value),max(t_pt.name::text))::character varying::text || ' '::text) || replace(array_agg(pav.name)::character varying::text, '{NULL}'::text, ''::text))::character varying AS new_name
	           FROM product_product t_pp
	             JOIN product_template t_pt ON t_pp.product_tmpl_id = t_pt.id
				 left join ir_translation it ON t_pt.id = it.res_id and it.name = 'product.template,name' and it.lang = 'es_PE' and it.state = 'translated'
			left join product_variant_combination pvc on pvc.product_product_id = t_pp.id
			left join product_template_attribute_value ptav on ptav.id = pvc.product_template_attribute_value_id
			left join product_attribute_value pav on pav.id = ptav.product_attribute_value_id
			group by t_pp.id
			) np on np.id = vst_kardex_sunat.product_id
						
		   where (fecha_num((vst_kardex_sunat.fecha - interval '5' hour)::date) between """+str(date_ini).replace('-','')+""" and """+str(date_fin).replace('-','')+""")    
		   and vst_kardex_sunat.location_id in """+str(almacenes)+""" and vst_kardex_sunat.product_id in """ +str(productos)+ """
				 and vst_kardex_sunat.company_id = """ +str(self.env.company.id)+ """
				order by vst_kardex_sunat.location_id,vst_kardex_sunat.product_id,vst_kardex_sunat.fecha,vst_kardex_sunat.esingreso,vst_kardex_sunat.stock_moveid,vst_kardex_sunat.nro
				)Total   """+si_existe+"""			
) A order by location_id,product_id,fechax
				
			""")
		total_all = self.env.cr.fetchall()


		self.send_message(text_report_linea+"Saldos Valorados<br/><center>Total lineas a procesar: "+str(len(total_all)) + "</center>")
		cont_report = 0
		import datetime
		tiempo_inicial = datetime.datetime.now()
		tiempo_pasado = [0,0]
		cprom_data = {}

		ingreso1 =0
		ingreso2 =0
		salida1 =0
		salida2 =0
		producto = 0
		almacen = 0
		array_grabar = None
		flag = False
		for xl in total_all:
			l = {
				'product_id':xl[0],
				'location_id':xl[1],
				'origen_usage':xl[2],
				'destino_usage':xl[3],
				'debit':xl[4],
				'credit':xl[5],
				'fechax':xl[6],
				'type_doc':xl[7],
				'serial':xl[8],
				'nro':xl[9],
				'numdoc_cuadre':xl[10],
				'nro_documento':xl[11],
				'name':xl[12],
				'operation_type':xl[13],
				'new_name':xl[14],
				'default_code':xl[15],
				'unidad':xl[16],
				'ingreso':xl[17],
				'salida':xl[18],
				'cadquiere':xl[19],
				'origen':xl[20],
				'destino':xl[21],
				'almacen':xl[22],
			}

			if producto == None:
				producto = l['product_id']
				almacen = l['almacen']
			if producto != 	l['product_id'] or almacen != l['almacen']:
				producto = l['product_id']
				almacen = l['almacen']	
				if array_grabar:			
					self.env.cr.execute("""
							update kardex_save_period set cprom = """ +str(array_grabar[6])+ """ where save_id = """ +str(self.id)+ """ and almacen = """ +str(array_grabar[7])+ """ and producto = """ +str(array_grabar[1])+ """
					 """)


			cont_report += 1
			if cont_report%300 == 0:
				tiempo_pasado = divmod((datetime.datetime.now()-tiempo_inicial).seconds,60)
				text_report = ""
				text_report = text_report_linea+ "<b>Saldos Valorados</b><br/><center>Total lineas a procesar: "+str(len(total_all)) + "</center><br/><center>Procesado:"+str(cont_report)+"/"+str(len(total_all))+"</center><br/> Tiempo Procesado: "+ str(tiempo_pasado[0])+" minutos " +str(tiempo_pasado[1]) + " segundos" 
				text_report += """<div id="myProgress" style="position: relative; width: 100%;  height: 30px;   background-color: white;">
				  <div id="myBar" style="position: absolute;  width: """+"%.2f"%(cont_report*100/len(total_all))+"""%;  height: 100%; background-color: #875A7B;">
				    <div id="label" style="text-align: center; line-height: 30px; color: white;">""" +"%.2f"%(cont_report*100/len(total_all))+ """%</div>
				  </div>
				</div>"""
				self.send_message(text_report)
				
			llave = (l['product_id'],l['location_id'])
			cprom_acum = [0,0]
			if llave in cprom_data:
				cprom_acum = cprom_data[llave]
			else:
				cprom_data[llave] = cprom_acum

			cprom_act_antes = cprom_data[llave][1] / cprom_data[llave][0] if cprom_data[llave][0] != 0 else 0

			data_temp = {}
			
			data_temp = {'origen':l['origen_usage'] or '','destino':l['destino_usage'] or ''}
			ingreso_v = 0
			egreso_v = 0
			if l['ingreso'] or l['debit']:
				if (data_temp['origen'] == 'internal' and data_temp['destino'] == 'internal') or (data_temp['origen'] == 'transit' and data_temp['destino'] == 'internal'):
					cprom_acum[0] = cprom_acum[0] + (l['ingreso'] if l['ingreso'] else 0) -  (l['salida'] if l['salida'] else 0)
					cprom_acum[1] = cprom_acum[1] + (l['debit'] if l['debit'] else 0) -  (l['credit'] if l['credit'] else 0)

					ingreso_v = (l['debit'] if l['debit'] else 0) 
				else:	
					cprom_acum[0] = cprom_acum[0] + (l['ingreso'] if l['ingreso'] else 0) -  (l['salida'] if l['salida'] else 0)
					cprom_acum[1] = cprom_acum[1] + (l['debit'] if l['debit'] else 0) -  (l['credit'] if l['credit'] else 0)

					ingreso_v = (l['debit'] if l['debit'] else 0) 
			else:
				if (data_temp['origen'] == 'internal' and data_temp['destino'] == 'supplier'):
					cprom_acum[0] = cprom_acum[0] -  (l['salida'] if l['salida'] else 0)
					cprom_acum[1] = cprom_acum[1] - (l['debit'] if l['debit'] else 0) - ( (l['credit'] if l['credit'] else 0) * (l['salida'] if l['salida'] else 0) )
					egreso_v = (l['credit'] if l['credit'] else 0) * (l['salida'] if l['salida'] else 0)
				else:
					if l['salida']:
						cprom_acum[0] = cprom_acum[0] + (l['ingreso'] if l['ingreso'] else 0) -  (l['salida'] if l['salida'] else 0)
						cprom_acum[1] = cprom_acum[1] - (l['salida'] if l['salida'] else 0)*(cprom_act_antes if cprom_act_antes else 0)

						egreso_v = (l['salida'] if l['salida'] else 0)*(cprom_act_antes if cprom_act_antes else 0)
					else:
						cprom_acum[0] = cprom_acum[0] + (l['ingreso'] if l['ingreso'] else 0) -  (l['salida'] if l['salida'] else 0)
						cprom_acum[1] = cprom_acum[1] - (l['credit'] if l['credit'] else 0)

						egreso_v = (l['credit'] if l['credit'] else 0)

			cprom_act = cprom_acum[1] / cprom_acum[0] if cprom_acum[0] != 0 else 0

			cprom_data[llave] = cprom_acum

			linea = []
			producto_obj = self.env['product.product'].browse(l['product_id'])
			
			linea.append( producto_obj.categ_id.name_get()[0][1] or '')
			linea.append( l['product_id'] if l['product_id'] else '')
			linea.append( l['new_name'] if l['new_name'] else '' )
			linea.append( l['unidad'] if l['unidad'] else '' )

			linea.append( cprom_acum[0] if len(cprom_acum)>1 and cprom_acum[0] else 0 )
			linea.append( cprom_acum[1] if len(cprom_acum)>1 and cprom_acum[1] else 0 )
			linea.append( (cprom_acum[1] if len(cprom_acum)>1 and cprom_acum[1] else 0) / (cprom_acum[0] if len(cprom_acum)>1 and cprom_acum[0] else 0) if (cprom_acum[0] if len(cprom_acum)>1 and cprom_acum[0] else 0) != 0 else 0 )

			linea.append( l['location_id'] if l['location_id'] else '' )
			array_grabar = linea.copy()

		if array_grabar:			
			self.env.cr.execute("""
					update kardex_save_period set cprom = """ +str(array_grabar[6])+ """ where save_id = """ +str(self.id)+ """ and almacen = """ +str(array_grabar[7])+ """ and producto = """ +str(array_grabar[1])+ """
			 """)
		lineas_mal = self.env["kardex.save.period"].sudo().search([("save_id","=",self.id),("cprom","<=",0)])
		for crear in lineas_mal:
			vals={
				"save_costo_bad_id":self.id,
				"almacen":crear.almacen.id,
				"producto":crear.producto.id,
				"stock":crear.stock,
				"lote":crear.lote.id,
				"cprom":crear.cprom
			}
			self.env["kardex.save.period"].sudo().create(vals)
		if len(self.lineas_cero_cero)==0:
			self.state = 'val_sol'
		else:
			msg="Corregir Costos Cero, o haga click en 'Aprobación Costo Cero'"
			return self.env['popup.it'].get_message(str(msg))


	def save_valorado_dolar(self):
		cad = ""
		lineas_mal_delete = self.env["kardex.save.period"].sudo().search([("save_costo_bad_id_dolar","=",self.id)])
		lineas_mal_delete.sudo().unlink()
		s_prod = [-1,-1,-1]
		s_loca = [-1,-1,-1]
		locat_ids = self.env['stock.location'].search( [('usage','in',('internal','inventory','transit','procurement','production'))] )
		lst_locations = locat_ids.ids
		
		productos='('
		almacenes='('

		lst_products = self.env['product.product'].with_context(active_test=False).search([]).ids

		
		if len(lst_products) == 0:
			raise UserError('No existen productos seleccionados')

		for producto in lst_products:
			productos=productos+str(producto)+','
			s_prod.append(producto)
		productos=productos[:-1]+')'
		for location in lst_locations:
			almacenes=almacenes+str(location)+','
			s_loca.append(location)
		almacenes=almacenes[:-1]+')'


		config = self.env['kardex.parameter'].search([('company_id','=',self.env.company.id)])

		date_fin = self.name.date_end
		date_ini = '%d-01-01' % ( config._get_anio_start(date_fin.year) )


		kardex_save_obj = self.env['kardex.save'].search([('company_id','=',self.env.company.id),('state','=','done'),('name.date_end','<',date_fin)]).sorted(lambda l: l.name.code , reverse=True)
		if len(kardex_save_obj)>0:
			kardex_save_obj = kardex_save_obj[0]
			date_ini = kardex_save_obj.name.date_end + timedelta(days=1)
		
		text_report_linea = ''
		if kardex_save_obj:
			text_report_linea = "<b>Se usara el saldo guardado: "+str(kardex_save_obj.name.code)+ " </b>"
			

		si_existe = ""
		if kardex_save_obj:
			si_existe = """union all


select 
				ksp.producto as product_id,
				ksp.almacen as location_id,
				'' as origen_usage,
				sl.usage as destino_usage,
				ksp.cprom_dolar * ksp.stock as debit,
				0 as credit,
				(fecha || ' 00:00:00')::timestamp as fechax,
				'' as type_doc,
				'' as serial,
				'' as nro,
				'' as numdoc_cuadre,
				'' as nro_documento,
				'Saldo Inicial' as name,
				'' as operation_type,
				pname.new_name,
				coalesce(pp.default_code,pt.default_code) as default_code,
				uu.name as unidad,
				ksp.stock as ingreso,
				0 as salida,
				ksp.cprom_dolar as cadquiere,
				'' as origen,
				sl.complete_name as destino,
				sl.complete_name as almacen

			from kardex_save_period ksp 
			inner join stock_location sl on sl.id = ksp.almacen
			inner join product_product pp on pp.id = ksp.producto
			inner join product_template pt on pt.id = pp.product_tmpl_id
			inner join uom_uom uu on uu.id = pt.uom_id
			inner join product_category pc on pc.id = pt.categ_id
			left join stock_production_lot spt on spt.id = ksp.lote
			 LEFT JOIN ( SELECT t_pp.id,
					((     coalesce(max(it.value),max(t_pt.name::text))::character varying::text || ' '::text) || replace(array_agg(pav.name)::character varying::text, '{NULL}'::text, ''::text))::character varying AS new_name
				   FROM product_product t_pp
					 JOIN product_template t_pt ON t_pp.product_tmpl_id = t_pt.id
					 left join ir_translation it ON t_pt.id = it.res_id and it.name = 'product.template,name' and it.lang = 'es_PE' and it.state = 'translated'
					 LEFT JOIN product_variant_combination pvc ON pvc.product_product_id = t_pp.id
					 LEFT JOIN product_template_attribute_value ptav ON ptav.id = pvc.product_template_attribute_value_id
					 LEFT JOIN product_attribute_value pav ON pav.id = ptav.product_attribute_value_id
				  GROUP BY t_pp.id) pname ON pname.id = pp.id
			 where save_id = """+str(kardex_save_obj.id)+"""
			 """

		text_report = "<b>Cargando Saldos Valorados (USD)</b><br/><center>Ejecutando SQL del kardex ... Espere por favor</center><br/>" + text_report_linea
		self.send_message(text_report)

		total_all = []


			

		self.env.cr.execute("""  
				select  
				product_id,
				location_id,
				origen_usage,
				destino_usage,
				debit,
				credit,
				fechax,
				type_doc,
				serial,
				nro,
				numdoc_cuadre,
				nro_documento,
				name,
				operation_type,
				new_name,
				default_code,
				unidad,
				ingreso,
				salida,
				cadquiere,
				origen,
				destino,
				almacen
		 from (
				select 
				product_id,
				location_id,
				origen_usage,
				destino_usage,
				debit,
				credit,
				fechax,
				type_doc,
				serial,
				nro,
				numdoc_cuadre,
				nro_documento,
				name,
				operation_type,
				new_name,
				default_code,
				unidad,
				ingreso,
				salida,
				cadquiere,
				origen,
				destino,
				almacen
				from (
	select vst_kardex_sunat.*,sp.name as doc_almac,sm.kardex_date as fecha_albaran,
	vst_kardex_sunat.fecha - interval '5' hour as fechax,sl_o.usage as origen_usage , sl_d.usage as destino_usage, np.new_name
				from vst_kardex_fisico_valorado_dolar as vst_kardex_sunat
	left join stock_move sm on sm.id = vst_kardex_sunat.stock_moveid
	left join stock_picking sp on sp.id = sm.picking_id

						left join stock_location sl_o on sl_o.id = sm.location_id
						left join stock_location sl_d on sl_d.id = sm.location_dest_id
	left join (
		select t_pp.id, 
	            ((     coalesce(max(it.value),max(t_pt.name::text))::character varying::text || ' '::text) || replace(array_agg(pav.name)::character varying::text, '{NULL}'::text, ''::text))::character varying AS new_name
	           FROM product_product t_pp
	             JOIN product_template t_pt ON t_pp.product_tmpl_id = t_pt.id
				 left join ir_translation it ON t_pt.id = it.res_id and it.name = 'product.template,name' and it.lang = 'es_PE' and it.state = 'translated'
			left join product_variant_combination pvc on pvc.product_product_id = t_pp.id
			left join product_template_attribute_value ptav on ptav.id = pvc.product_template_attribute_value_id
			left join product_attribute_value pav on pav.id = ptav.product_attribute_value_id
			group by t_pp.id
			) np on np.id = vst_kardex_sunat.product_id
						
		   where (fecha_num((vst_kardex_sunat.fecha - interval '5' hour)::date) between """+str(date_ini).replace('-','')+""" and """+str(date_fin).replace('-','')+""")    
		   and vst_kardex_sunat.location_id in """+str(almacenes)+""" and vst_kardex_sunat.product_id in """ +str(productos)+ """
				 and vst_kardex_sunat.company_id = """ +str(self.env.company.id)+ """
				order by vst_kardex_sunat.location_id,vst_kardex_sunat.product_id,vst_kardex_sunat.fecha,vst_kardex_sunat.esingreso,vst_kardex_sunat.stock_moveid,vst_kardex_sunat.nro
				)Total   """+si_existe+"""			
) A order by location_id,product_id,fechax
				
			""")
		total_all = self.env.cr.fetchall()


		self.send_message(text_report_linea+"Saldos Valorados (USD)<br/><center>Total lineas a procesar: "+str(len(total_all)) + "</center>")
		cont_report = 0
		import datetime
		tiempo_inicial = datetime.datetime.now()
		tiempo_pasado = [0,0]
		cprom_data = {}

		ingreso1 =0
		ingreso2 =0
		salida1 =0
		salida2 =0
		producto = 0
		almacen = 0
		array_grabar = None
		flag = False
		for xl in total_all:
			l = {
				'product_id':xl[0],
				'location_id':xl[1],
				'origen_usage':xl[2],
				'destino_usage':xl[3],
				'debit':xl[4],
				'credit':xl[5],
				'fechax':xl[6],
				'type_doc':xl[7],
				'serial':xl[8],
				'nro':xl[9],
				'numdoc_cuadre':xl[10],
				'nro_documento':xl[11],
				'name':xl[12],
				'operation_type':xl[13],
				'new_name':xl[14],
				'default_code':xl[15],
				'unidad':xl[16],
				'ingreso':xl[17],
				'salida':xl[18],
				'cadquiere':xl[19],
				'origen':xl[20],
				'destino':xl[21],
				'almacen':xl[22],
			}

			if producto == None:
				producto = l['product_id']
				almacen = l['almacen']
			if producto != 	l['product_id'] or almacen != l['almacen']:
				producto = l['product_id']
				almacen = l['almacen']	
				if array_grabar:			
					self.env.cr.execute("""
							update kardex_save_period set cprom_dolar = """ +str(array_grabar[6])+ """ where save_id = """ +str(self.id)+ """ and almacen = """ +str(array_grabar[7])+ """ and producto = """ +str(array_grabar[1])+ """
					 """)


			cont_report += 1
			if cont_report%300 == 0:
				tiempo_pasado = divmod((datetime.datetime.now()-tiempo_inicial).seconds,60)
				text_report = ""
				text_report = text_report_linea+ "<b>Saldos Valorados (USD)</b><br/><center>Total lineas a procesar: "+str(len(total_all)) + "</center><br/><center>Procesado:"+str(cont_report)+"/"+str(len(total_all))+"</center><br/> Tiempo Procesado: "+ str(tiempo_pasado[0])+" minutos " +str(tiempo_pasado[1]) + " segundos" 
				text_report += """<div id="myProgress" style="position: relative; width: 100%;  height: 30px;   background-color: white;">
				  <div id="myBar" style="position: absolute;  width: """+"%.2f"%(cont_report*100/len(total_all))+"""%;  height: 100%; background-color: #875A7B;">
				    <div id="label" style="text-align: center; line-height: 30px; color: white;">""" +"%.2f"%(cont_report*100/len(total_all))+ """%</div>
				  </div>
				</div>"""
				self.send_message(text_report)
				
			llave = (l['product_id'],l['location_id'])
			cprom_acum = [0,0]
			if llave in cprom_data:
				cprom_acum = cprom_data[llave]
			else:
				cprom_data[llave] = cprom_acum

			cprom_act_antes = cprom_data[llave][1] / cprom_data[llave][0] if cprom_data[llave][0] != 0 else 0

			data_temp = {}
			
			data_temp = {'origen':l['origen_usage'] or '','destino':l['destino_usage'] or ''}
			ingreso_v = 0
			egreso_v = 0
			if l['ingreso'] or l['debit']:
				if (data_temp['origen'] == 'internal' and data_temp['destino'] == 'internal') or (data_temp['origen'] == 'transit' and data_temp['destino'] == 'internal'):
					cprom_acum[0] = cprom_acum[0] + (l['ingreso'] if l['ingreso'] else 0) -  (l['salida'] if l['salida'] else 0)
					cprom_acum[1] = cprom_acum[1] + (l['debit'] if l['debit'] else 0) -  (l['credit'] if l['credit'] else 0)

					ingreso_v = (l['debit'] if l['debit'] else 0) 
				else:	
					cprom_acum[0] = cprom_acum[0] + (l['ingreso'] if l['ingreso'] else 0) -  (l['salida'] if l['salida'] else 0)
					cprom_acum[1] = cprom_acum[1] + (l['debit'] if l['debit'] else 0) -  (l['credit'] if l['credit'] else 0)

					ingreso_v = (l['debit'] if l['debit'] else 0) 
			else:
				if (data_temp['origen'] == 'internal' and data_temp['destino'] == 'supplier'):
					cprom_acum[0] = cprom_acum[0] -  (l['salida'] if l['salida'] else 0)
					cprom_acum[1] = cprom_acum[1] - (l['debit'] if l['debit'] else 0) - ( (l['credit'] if l['credit'] else 0) * (l['salida'] if l['salida'] else 0) )
					egreso_v = (l['credit'] if l['credit'] else 0) * (l['salida'] if l['salida'] else 0)
				else:
					if l['salida']:
						cprom_acum[0] = cprom_acum[0] + (l['ingreso'] if l['ingreso'] else 0) -  (l['salida'] if l['salida'] else 0)
						cprom_acum[1] = cprom_acum[1] - (l['salida'] if l['salida'] else 0)*(cprom_act_antes if cprom_act_antes else 0)

						egreso_v = (l['salida'] if l['salida'] else 0)*(cprom_act_antes if cprom_act_antes else 0)
					else:
						cprom_acum[0] = cprom_acum[0] + (l['ingreso'] if l['ingreso'] else 0) -  (l['salida'] if l['salida'] else 0)
						cprom_acum[1] = cprom_acum[1] - (l['credit'] if l['credit'] else 0)

						egreso_v = (l['credit'] if l['credit'] else 0)

			cprom_act = cprom_acum[1] / cprom_acum[0] if cprom_acum[0] != 0 else 0

			cprom_data[llave] = cprom_acum

			linea = []
			producto_obj = self.env['product.product'].browse(l['product_id'])
			
			linea.append( producto_obj.categ_id.name_get()[0][1] or '')
			linea.append( l['product_id'] if l['product_id'] else '')
			linea.append( l['new_name'] if l['new_name'] else '' )
			linea.append( l['unidad'] if l['unidad'] else '' )

			linea.append( cprom_acum[0] if len(cprom_acum)>1 and cprom_acum[0] else 0 )
			linea.append( cprom_acum[1] if len(cprom_acum)>1 and cprom_acum[1] else 0 )
			linea.append( (cprom_acum[1] if len(cprom_acum)>1 and cprom_acum[1] else 0) / (cprom_acum[0] if len(cprom_acum)>1 and cprom_acum[0] else 0) if (cprom_acum[0] if len(cprom_acum)>1 and cprom_acum[0] else 0) != 0 else 0 )

			linea.append( l['location_id'] if l['location_id'] else '' )
			array_grabar = linea.copy()
		
		if array_grabar:			
			self.env.cr.execute("""
					update kardex_save_period set cprom_dolar = """ +str(array_grabar[6])+ """ where save_id = """ +str(self.id)+ """ and almacen = """ +str(array_grabar[7])+ """ and producto = """ +str(array_grabar[1])+ """
			 """)
		self.corriovalorizado=True
		lineas_mal = self.env["kardex.save.period"].sudo().search([("save_id","=",self.id),("cprom_dolar","<=",0)])
		for crear in lineas_mal:
			vals={
				"save_costo_bad_id_dolar":self.id,
				"almacen":crear.almacen.id,
				"producto":crear.producto.id,
				"stock":crear.stock,
				"lote":crear.lote.id,
				"cprom":crear.cprom
			}
			self.env["kardex.save.period"].sudo().create(vals)
		if len(self.lineas_cero_cero_dolar)==0:
			self.state = 'val_dol'
		else:
			msg="Corregir Costos Dolares Cero, o haga click en 'Aprobación Costo Cero Dolar'"
			return self.env['popup.it'].get_message(str(msg))




	def save_fisico(self):
		#blanquear
		self.env.cr.execute("""
			delete from kardex_save_period where save_id = """ +str( self.id ) )
		self.env.cr.execute("""
			delete from kardex_save_period where save_bad_id = """ +str( self.id ) )
		self.env.cr.execute("""
			delete from kardex_save_period where save_costo_bad_id = """ +str( self.id ) )
		self.env.cr.execute("""
			delete from kardex_save_period where save_costo_bad_id_dolar = """ +str( self.id ) )
		self.env.cr.execute("""
			delete from kardex_save_period_error where save_id = """ +str( self.id ) )

		import datetime
		self.date = str(fields.Datetime.context_timestamp(self.with_context(tz=self.env.user.tz), datetime.datetime.now()))[:19]


		s_prod = [-1,-1,-1]
		s_loca = [-1,-1,-1]
		locat_ids = self.env['stock.location'].search( [('usage','in',('internal','internal'))] )
		lst_locations = locat_ids.ids
		productos='{'
		almacenes='{'
		lst_products = self.env['product.product'].with_context(active_test=False).search([]).ids
		if len(lst_products) == 0:
			raise UserError('Alerta','No existen productos seleccionados')

		for producto in lst_products:
			productos=productos+str(producto)+','
			s_prod.append(producto)
		productos=productos[:-1]+'}'
		for location in lst_locations:
			almacenes=almacenes+str(location)+','
			s_loca.append(location)
		almacenes=almacenes[:-1]+'}'

		config = self.env['kardex.parameter'].search([('company_id','=',self.env.company.id)])

		date_fin = self.name.date_end
		date_ini = '%d-01-01' % ( config._get_anio_start(date_fin.year) )

		kardex_save_obj = self.env['kardex.save'].search([('company_id','=',self.env.company.id),('state','=','done'),('name.date_end','<',self.name.date_start)]).sorted(lambda l: l.name.code , reverse=True)
		if len(kardex_save_obj)>0:
			kardex_save_obj = kardex_save_obj[0]
			date_ini = kardex_save_obj.name.date_end + timedelta(days=1)
			
		
		si_existe = ""
		if kardex_save_obj:
			si_existe = """ select ksp.almacen as alm_id, ksp.producto as p_id,pt.categ_id as categoria_id, '"""+str(kardex_save_obj.name.date_end)+"""'::date as fecha,
			'SALDO INICIAL' as origen, sl.complete_name as destino, sl.complete_name as almacen, ksp.stock as entrada, 0 as salida, null as stock_move,
			'' as motivo_guia, pname.new_name as producto, 'done' as estado, 'Saldo Inicial' as name, coalesce(pp.default_code,pt.default_code) as cod_pro,
			pc.name as categoria, uu.name as unidad, ksp.producto as product_id, ksp.almacen as almacen_id, spt.name as lote, spt.id as lote_id
			from kardex_save_period ksp 
			inner join stock_location sl on sl.id = ksp.almacen
			inner join product_product pp on pp.id = ksp.producto
			inner join product_template pt on pt.id = pp.product_tmpl_id
			inner join uom_uom uu on uu.id = pt.uom_id
			inner join product_category pc on pc.id = pt.categ_id
			left join stock_production_lot spt on spt.id = ksp.lote
			 LEFT JOIN ( SELECT t_pp.id,
					((     coalesce(max(it.value),max(t_pt.name::text))::character varying::text || ' '::text) || replace(array_agg(pav.name)::character varying::text, '{NULL}'::text, ''::text))::character varying AS new_name
				   FROM product_product t_pp
					 JOIN product_template t_pt ON t_pp.product_tmpl_id = t_pt.id
					 left join ir_translation it ON t_pt.id = it.res_id and it.name = 'product.template,name' and it.lang = 'es_PE' and it.state = 'translated'
					 LEFT JOIN product_variant_combination pvc ON pvc.product_product_id = t_pp.id
					 LEFT JOIN product_template_attribute_value ptav ON ptav.id = pvc.product_template_attribute_value_id
					 LEFT JOIN product_attribute_value pav ON pav.id = ptav.product_attribute_value_id
				  GROUP BY t_pp.id) pname ON pname.id = pp.id
			 where save_id = """+str(kardex_save_obj.id)+"""
			union all """

		self.env.cr.execute("""
			select 
			vstf.p_id,
			vstf.alm_id,	
			coalesce(sum(coalesce(vstf.entrada,0)),0) -  coalesce(sum(coalesce(vstf.salida,0)),0),
			vstf.lote_id
			from
			(""" +si_existe+ """	
			select location_dest_id as alm_id, product_id as p_id, categoria_id, vst_kardex_fisico.date as fecha,u_origen as origen, u_destino as destino, u_destino as almacen, vst_kardex_fisico.product_qty as entrada, 0 as salida,vst_kardex_fisico.id  as stock_move,vst_kardex_fisico.guia as motivo_guia, producto,vst_kardex_fisico.estado,vst_kardex_fisico.name, cod_pro, categoria, unidad,product_id,location_dest_id as almacen_id, lote,lote_id from vst_kardex_fisico_lote() as vst_kardex_fisico where company_id = """+str(self.env.company.id)+"""
			and (date - interval '5' hour)::date >='""" +str(date_ini)+ """' and (date - interval '5' hour)::date <='""" +str(date_fin)+ """'			
			union all
			select location_id as alm_id, product_id as p_id, categoria_id, vst_kardex_fisico.date as fecha,u_origen as origen, u_destino as destino, u_origen as almacen, 0 as entrada, vst_kardex_fisico.product_qty as salida,vst_kardex_fisico.id  as stock_move ,vst_kardex_fisico.guia as motivo_guia ,producto ,vst_kardex_fisico.estado,vst_kardex_fisico.name, cod_pro, categoria, unidad,product_id, location_id as almacen_id, lote, lote_id from vst_kardex_fisico_lote() as vst_kardex_fisico where company_id = """+str(self.env.company.id)+"""
			and (date - interval '5' hour)::date >='""" +str(date_ini)+ """' and (date - interval '5' hour)::date <='""" +str(date_fin)+ """'			
			) as vstf
			left join stock_production_lot spl on spl.id = vstf.lote_id
			where 
			vstf.product_id in """ +str(tuple(s_prod))+ """
			and vstf.almacen_id in """ +str(tuple(s_loca))+ """
			and vstf.estado = 'done'
			group by
			producto,cod_pro,categoria_id, p_id, alm_id,lote,lote_id
			having coalesce(sum(coalesce(vstf.entrada,0)),0) -  coalesce(sum(coalesce(vstf.salida,0)),0) != 0;
		""")
		for line in self.env.cr.fetchall():

			self.env['kardex.save.period'].create({
						'save_id':self.id,
						'producto': line[0],
						'almacen': line[1],
						'fecha':self.name.date_end,
						'stock': line[2],
						'lote': line[3],
						'cprom': 0,
						'cprom_dolar': 0,
					})
			if round(line[2],2)<0:
				self.env['kardex.save.period'].create({
					'save_bad_id':self.id,
					'producto': line[0],
					'almacen': line[1],
					'fecha':self.name.date_end,
					'stock': line[2],
					'lote': line[3],
					'cprom': 0,
					'cprom_dolar': 0,
					})
		self.env.cr.execute("""
			select 
			vstf.p_id,
			vstf.alm_id,	
			coalesce(vstf.entrada,0) -  coalesce(vstf.salida,0),
			vstf.lote_id,
			vstf.code_sunat,
			vstf.ubidestino,
			vstf.ubiorigen,
			vstf.picking,
			vstf.sunat_name
			from
			(""" +""+ """
			select vst_kardex_fisico.location_dest_id as alm_id, vst_kardex_fisico.product_id as p_id, vst_kardex_fisico.categoria_id, vst_kardex_fisico.date as fecha,vst_kardex_fisico.u_origen as origen, vst_kardex_fisico.u_destino as destino, vst_kardex_fisico.u_destino as almacen, vst_kardex_fisico.product_qty as entrada, 0 as salida,vst_kardex_fisico.id  as stock_move,vst_kardex_fisico.guia as motivo_guia, producto,vst_kardex_fisico.estado,vst_kardex_fisico.name, vst_kardex_fisico.cod_pro, vst_kardex_fisico.categoria, vst_kardex_fisico.unidad,vst_kardex_fisico.product_id,vst_kardex_fisico.location_dest_id as almacen_id, vst_kardex_fisico.lote,vst_kardex_fisico.lote_id,slo.usage as ubiorigen,sld.usage as ubidestino,tok.code as code_sunat, tok.name as sunat_name,sp.id as picking  from vst_kardex_fisico_lote() as vst_kardex_fisico 
			left join stock_move sm on sm.id = vst_kardex_fisico.id
			left join stock_picking sp on sp.id = sm.picking_id
			left join stock_location slo on slo.id=sm.location_id
			left join stock_location sld on sld.id=sm.location_dest_id
			left join type_operation_kardex tok on tok.id=sp.type_operation_sunat_id

			where vst_kardex_fisico.company_id = """+str(self.env.company.id)+"""
			and (vst_kardex_fisico.date - interval '5' hour)::date >='""" +str(date_ini)+ """' and (vst_kardex_fisico.date - interval '5' hour)::date <='""" +str(date_fin)+ """'
   
			union all
			select vst_kardex_fisico.location_id as alm_id, vst_kardex_fisico.product_id as p_id, vst_kardex_fisico.categoria_id, vst_kardex_fisico.date as fecha,vst_kardex_fisico.u_origen as origen, vst_kardex_fisico.u_destino as destino, vst_kardex_fisico.u_origen as almacen, 0 as entrada, vst_kardex_fisico.product_qty as salida,vst_kardex_fisico.id  as stock_move ,vst_kardex_fisico.guia as motivo_guia ,producto ,vst_kardex_fisico.estado,vst_kardex_fisico.name, vst_kardex_fisico.cod_pro, vst_kardex_fisico.categoria, vst_kardex_fisico.unidad,vst_kardex_fisico.product_id, vst_kardex_fisico.location_id as almacen_id, vst_kardex_fisico.lote, vst_kardex_fisico.lote_id,slo.usage as ubiorigen,sld.usage as ubidestino,tok.code as code_sunat, tok.name as sunat_name,sp.id as picking from vst_kardex_fisico_lote() as vst_kardex_fisico 
			left join stock_move sm on sm.id = vst_kardex_fisico.id
			left join stock_picking sp on sp.id = sm.picking_id
			left join stock_location slo on slo.id=sm.location_id
			left join stock_location sld on sld.id=sm.location_dest_id
			left join type_operation_kardex tok on tok.id=sp.type_operation_sunat_id

   			where vst_kardex_fisico.company_id = """+str(self.env.company.id)+"""
			and (vst_kardex_fisico.date - interval '5' hour)::date >='""" +str(date_ini)+ """' and (vst_kardex_fisico.date - interval '5' hour)::date <='""" +str(date_fin)+ """'			
			) as vstf
			left join stock_production_lot spl on spl.id = vstf.lote_id
			where 
			vstf.product_id in """ +str(tuple(s_prod))+ """
			and vstf.almacen_id in """ +str(tuple(s_loca))+ """
			and vstf.estado = 'done';
			""")
		vls={
			"internal":"Ubicación Interna",
			"supplier":"Ubicación de Proveedor",
			"customer":"Ubicación de Cliente"
		}
		for line in self.env.cr.fetchall():
			if line[4]:
				sunat=str(line[4])
				sunat_name=str(line[8])
				location_origen = line[6]
				location_destino = line[5]
				if (location_origen == "internal" and location_destino == "supplier" and sunat != "06") or (location_origen == "customer" and location_destino == "internal" and sunat != "05") or (location_origen == "supplier" and location_destino == "internal" and sunat != "02") or (location_origen == "internal" and location_destino == "customer" and sunat != "01"):
					sunat_esperado = ""
					if location_origen == "internal" and location_destino == "supplier" and sunat != "06":
						sunat_esperado = "06 - DEVOLUCION ENTREGADA"
					elif location_origen == "customer" and location_destino == "internal" and sunat != "05":
						sunat_esperado = "05 - DEVOLUCION RECIBIDA"
					elif location_origen == "supplier" and location_destino == "internal" and sunat != "02":
						sunat_esperado = "02 - COMPRA NACIONAL"
					else:
						sunat_esperado = "01 - VENTA NACIONAL"
					self.env['kardex.save.period.error'].create({
						'save_id':self.id,
						'sunat_esperado':sunat_esperado,
						'producto': line[0],
						'almacen': vls[location_origen],
						'almacen_dest':vls[location_destino],
						'sunat':sunat+" - " + sunat_name,
						'lote': line[3],
						'picking_id':line[7]
					})
		if len(self.lineas_cero)>0:
			self.state = 'draft'
		else:
			self.state = 'first'
		if len(self.lineas_mal)>0:
			if not self.user_aprob_sunat_oper.id:
				self.state = 'draft'
		msg=False
		if len(self.lineas_cero)>0:
			msg = "Imposible avanzar, Corregir Negativos"
		if not msg:
			if len(self.lineas_mal)>0:
				msg = "Verifique Operaciones SUNAT o haga click en 'Aprobación Operacion SUNAT'"
		if msg:
			return self.env['popup.it'].get_message(str(msg))



	def draft(self):
		self.state = 'draft'
		self.env.cr.execute("""

			delete from kardex_save_period where save_id = """ +str( self.id ) )
		self.env.cr.execute("""

			delete from kardex_save_period where save_bad_id = """ +str( self.id ) )
		self.env.cr.execute("""
			delete from kardex_save_period where save_costo_bad_id = """ +str( self.id ) )		
		self.env.cr.execute("""
			delete from kardex_save_period where save_costo_bad_id_dolar = """ +str( self.id ) )		

		self.env.cr.execute("""
			delete from kardex_save_period_error where save_id = """ +str( self.id ) )


	def aprobar_costo_cero(self):
		return True

	def aprobar_oper_sunat(self):
		return True














		
