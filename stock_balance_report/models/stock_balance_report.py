# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError

from datetime import datetime, timedelta


class stock_balance_report_wizard(models.TransientModel):
	_name = 'stock.balance.report.wizard'
	_description = "stock balance report wizard"

	def get_stock_lote(self):
		return self.env['stock.balance.report'].with_context({'res_model_it':'stock.balance.report.wizard','id_it':self.id}).get_balance_view()



class StockBalanceReport(models.Model):
	_name = 'stock.balance.report'
	_description = 'Balance Report'

	producto = fields.Many2one('product.product',string='N.Producto',store=True)
	codigo = fields.Char(related='producto.default_code',string='Cod. Producto',store=True)
	almacen = fields.Many2one('stock.location',string=u'N.Almacén',store=True)
	entrada = fields.Float(string='Stock', digits=(12,2),store=True)
	salida = fields.Float(string='Salida', digits=(12,2),store=True)
	saldo = fields.Float(string='Disponible', digits=(12,2),store=True)
	unidad = fields.Many2one(related='producto.uom_id',string='Unidad',store=True)
	categoria_1 = fields.Char(related='producto.categ_id.name',string='Categoria 1',store=True)
	categoria_2 = fields.Char(related='producto.categ_id.parent_id.name',string='Categoria 2',store=True)
	categoria_3 = fields.Char(related='producto.categ_id.parent_id.parent_id.name',string='Categoria 3',store=True)

	reservado = fields.Float(string='Reservado', digits=(12,2),store=True)
	product_id = fields.Many2one('product.product','Producto',store=True)
	almacen_id = fields.Many2one('stock.location','Almacen',store=True)

	def get_balance_view(self):

		tiempo_inicial = datetime.now()
		self.search([]).unlink()
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

		date_fin = self.env.context['date_final'] if 'date_final' in self.env.context else fields.Date.context_today(self)
		date_ini = '%d-01-01' % ( config._get_anio_start(date_fin.year) )

		kardex_save_obj = self.env['kardex.save'].search([('company_id','=',self.env.company.id),('state','=','done'),('name.date_end','<',date_fin)]).sorted(lambda l: l.name.code , reverse=True)
		if len(kardex_save_obj)>0:
			kardex_save_obj = kardex_save_obj[0]
			date_ini = kardex_save_obj.name.date_end + timedelta(days=1)



		#tiempo_pasado = divmod((datetime.now()-tiempo_inicial).seconds,60)
		text_report = "<b>Generando Reporte de Saldos</b><br/>"
		if kardex_save_obj:
			text_report +="Calculando con Saldos Guardados para el periodo: " + kardex_save_obj.name.code + "<br/>"

		text_report_line = text_report + u"---Extrayendo información de la Base de Datos---"

		self.send_message(text_report_line)

		si_existe = ""
		if kardex_save_obj:
			si_existe = """ select ksp.almacen as alm_id, ksp.producto as p_id,pt.categ_id as categoria_id, '"""+str(kardex_save_obj.name.date_end)+"""'::date as fecha,
			'SALDO INICIAL' as origen, sl.complete_name as destino, sl.complete_name as almacen, ksp.stock as entrada, 0 as salida, null as stock_move,
			'' as motivo_guia, pname.new_name as producto, 'done' as estado, 'Saldo Inicial' as name, coalesce(pp.default_code,pt.default_code) as cod_pro,
			pc.name as categoria, uu.name as unidad, ksp.producto as product_id, ksp.almacen as almacen_id
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

			#for alm in kardex_save_obj.lineas:
			#	self.env.cr.execute(""" select sum(product_uom_qty) 
			#		from stock_move_line 
			#		inner join stock_production_lot  on stock_production_lot.id = stock_move_line.lot_id 
			#		where stock_production_lot.id = """ +str(alm.lote.id)+ """ and 
			#		stock_move_line.location_id = """ +str(alm.almacen.id)+ """
			#		and stock_move_line.product_id = """ +str(alm.producto.id)+ """ and 
			#		stock_move_line.state in ('partially_available','assigned') """)
			#	cont1 = 0
			#	for ex in self.env.cr.fetchall():
			#		cont1 = ex[0]
			#	data[(alm.almacen.id,alm.producto.id,alm.lote.id)] = [alm.almacen.id,alm.producto.id,alm.stock,alm.lote.id,cont1]


		self.env.cr.execute("""
			select 
			vstf.p_id,
			vstf.alm_id,
			coalesce(sum(coalesce(vstf.entrada,0)),0) -  coalesce(sum(coalesce(vstf.salida,0)),0),
			0 as salida,
			coalesce(sum(coalesce(vstf.entrada,0)),0) -  coalesce(sum(coalesce(vstf.salida,0)),0) - coalesce(max(reservado.reservado),0),
			coalesce(max(reservado.reservado),0),
			vstf.p_id,
			vstf.alm_id
			from
			( """ +si_existe+ """			
			select location_dest_id as alm_id, product_id as p_id, categoria_id, vst_kardex_fisico.date as fecha,u_origen as origen, u_destino as destino, u_destino as almacen, vst_kardex_fisico.product_qty as entrada, 0 as salida,vst_kardex_fisico.id  as stock_move,vst_kardex_fisico.guia as motivo_guia, producto,vst_kardex_fisico.estado,vst_kardex_fisico.name, cod_pro, categoria, unidad,product_id,location_dest_id as almacen_id from vst_kardex_fisico_lote() as vst_kardex_fisico where company_id = """+str(self.env.company.id)+"""
			and (date - interval '5' hour)::date >='""" +str(date_ini)+ """' and (date - interval '5' hour)::date <='""" +str(date_fin)+ """'
			union all
			select location_id as alm_id, product_id as p_id, categoria_id, vst_kardex_fisico.date as fecha,u_origen as origen, u_destino as destino, u_origen as almacen, 0 as entrada, vst_kardex_fisico.product_qty as salida,vst_kardex_fisico.id  as stock_move ,vst_kardex_fisico.guia as motivo_guia ,producto ,vst_kardex_fisico.estado,vst_kardex_fisico.name, cod_pro, categoria, unidad,product_id, location_id as almacen_id from vst_kardex_fisico_lote() as vst_kardex_fisico where company_id = """+str(self.env.company.id)+"""
			and (date - interval '5' hour)::date >='""" +str(date_ini)+ """' and (date - interval '5' hour)::date <='""" +str(date_fin)+ """'
			) as vstf
			left join (
				select stock_move_line.location_id,sum(stock_move_line.product_uom_qty) as reservado, stock_move_line.product_id  from stock_move_line where stock_move_line.state in ('partially_available','assigned') 
				group by stock_move_line.location_id, stock_move_line.product_id
			) reservado on reservado.product_id = vstf.p_id and reservado.location_id = vstf.alm_id
			where 
			vstf.product_id in """ +str(tuple(s_prod))+ """
			and vstf.almacen_id in """ +str(tuple(s_loca))+ """
			and vstf.estado = 'done'
			group by
			producto,cod_pro,categoria_id, p_id, alm_id
			having coalesce(sum(coalesce(vstf.entrada,0)),0) -  coalesce(sum(coalesce(vstf.salida,0)),0) != 0
			;
		""")

		todos = self.env.cr.fetchall()

		text_report_line = text_report + u"---Se procesaran: "+ str(len(todos)) + " lineas---"
		self.send_message(text_report_line)
		cont_report = 0

		for item in todos:
			data = {
				'producto':item[0],
				'almacen':item[1],
				'entrada':item[2],
				'salida':item[3],
				'saldo':item[4],
				'reservado':item[5],
				'product_id':item[6],
				'almacen_id':item[7],
			}
			self.env['stock.balance.report'].create(data)

			if cont_report%300 == 0:
				tiempo_pasado = divmod((datetime.now()-tiempo_inicial).seconds,60)
				
				text_report_line = "<b>Generando Saldos.</b><br/><center>Total lineas a procesar: "+str(len(todos)) + "</center><br/><center>Procesado:"+str(cont_report)+"/"+str(len(todos))+"</center><br/> Tiempo Procesado: "+ str(tiempo_pasado[0])+" minutos " +str(tiempo_pasado[1]) + " segundos" 
				text_report_line += """<div id="myProgress" style="position: relative; width: 100%;  height: 30px;   background-color: white;">
				  <div id="myBar" style="position: absolute;  width: """+"%.2f"%(cont_report*100/len(todos))+"""%;  height: 100%; background-color: #875A7B;">
				    <div id="label" style="text-align: center; line-height: 30px; color: white;">""" +"%.2f"%(cont_report*100/len(todos))+ """%</div>
				  </div>
				</div>"""
				self.send_message(text_report)

			cont_report += 1
		
		#for line in self.env.cr.fetchall():
		#	if (line[14],line[13],line[16]) in data:
		#		data[(line[14],line[13],line[16])][2] += (line[10] or 0) - (line[11] or 0)
		#	else:
		#		data[(line[14],line[13],line[16])] = [line[14],line[13], (line[10] or 0) - (line[11] or 0) , line[16], line[17],line[18] ]


		#for final in data:
		#	self.create({
		#				'producto': data[final][1],
		#				'almacen': data[final][0],
		#				'entrada': data[final][2],
		#				'salida': 0,
		#				'saldo': data[final][2]- (data[final][4] or 0),
		#				'lote': data[final][3],
		#				'reservado': data[final][4],
		#				'product_id': data[final][1],
		#				'almacen_id': data[final][0],
		#			})

		return {
			'name': 'Reporte de Saldos',
			'type': 'ir.actions.act_window',
			'res_model': 'stock.balance.report',
			'view_mode': 'tree,pivot,graph',
			'views': [(False, 'tree'), (False, 'pivot'), (False, 'graph')]
		}
