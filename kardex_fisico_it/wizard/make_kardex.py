# -*- coding: utf-8 -*-
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
import time
import odoo.addons.decimal_precision as dp
from openerp.osv import osv
import base64
from odoo import models, fields, api
from odoo.exceptions import UserError
import codecs
from datetime import timedelta

values = {}

class tree_view_kardex_fisico(models.Model):
	_name = 'tree.view.kardex.fisico'
	_description = "tree view kardex fisico"
	_auto = False

	u_origen = fields.Char(string=u'Ubicación Origen')
	u_destino = fields.Char(string=u'Ubicación Destino')
	almacen = fields.Char(string=u'Almacén')
	t_opera = fields.Char(string=u'Tipo de Operación')
	categoria = fields.Char(string=u'Categoría')
	producto = fields.Char(string=u'Producto')
	cod_pro = fields.Char(string=u'Codigo P.')
	unidad = fields.Char(string=u'Unidad')
	fecha = fields.Char(string=u'Fecha')
	doc_almacen = fields.Char(string=u'Doc. Almacén')
	entrada = fields.Float(string=u'Entrada',digits=(12,2))
	salida = fields.Float(string=u'Salida',digits=(12,2))

	def init(self):
		self.env.cr.execute(""" create or replace view """+self._table+""" as (select 1 as campo1) """)

class product_template(models.Model):
	_inherit = 'product.template'

	def get_kardex_fisico(self):
		products = self.env['product.product'].search([('product_tmpl_id','=',self.id)])
		if len(products)>1:
			raise UserError('Existen variantes de productos, debe sacarse el kardex desde variante de producto.')
		return {
			'context':{'active_id':products[0].id},
			'name': 'Kardex Fisico',
			'type': 'ir.actions.act_window',
			'res_model': 'make.kardex.product',
			'view_mode': 'form',
			'views': [(False, 'form')],
			'target': 'new',
		}

class product_product(models.Model):
	_inherit = 'product.product'

	def get_kardex_fisico(self):
		return {
			'context':{'active_id':self.id},
			'name': 'Kardex Fisico',
			'type': 'ir.actions.act_window',
			'res_model': 'make.kardex.product',
			'view_mode': 'form',
			'views': [(False, 'form')],
			'target': 'new',
		}

class make_kardex(models.TransientModel):
	_name = "make.kardex"
	_description = "marke kardex"

	fini= fields.Date('Fecha inicial',required=True)
	ffin= fields.Date('Fecha final',required=True)
	products_ids=fields.Many2many('product.product','rel_wiz_kardex','product_id','kardex_id')
	location_ids=fields.Many2many('stock.location','rel_kardex_location','location_id','kardex_id','Ubicacion',required=True)
	allproducts=fields.Boolean('Todos los productos',default=True)
	destino = fields.Selection([('csv','CSV'),('crt','Pantalla')],'Destino')
	check_fecha = fields.Boolean('Editar Fecha')
	alllocations = fields.Boolean('Todos los almacenes',default=True)

	fecha_ini_mod = fields.Date('Fecha Inicial')
	fecha_fin_mod = fields.Date('Fecha Final')
	analizador = fields.Boolean('Analizador')

	@api.onchange('fecha_ini_mod')
	def onchange_fecha_ini_mod(self):
		self.fini = self.fecha_ini_mod

	@api.onchange('fecha_fin_mod')
	def onchange_fecha_fin_mod(self):
		self.ffin = self.fecha_fin_mod

	@api.model
	def default_get(self, fields):
		res = super(make_kardex, self).default_get(fields)
		import datetime
		fecha_hoy = str(datetime.datetime.now())[:10]
		fecha_inicial = fecha_hoy[:4] + '-01-01'
		res.update({'fecha_ini_mod':fecha_inicial})
		res.update({'fecha_fin_mod':fecha_hoy})
		res.update({'fini':fecha_inicial})
		res.update({'ffin':fecha_hoy})
		#locat_ids = self.pool.get('stock.location').search(cr, uid, [('usage','in',('internal','inventory','transit','procurement','production'))])
		locat_ids = self.env['stock.location'].search([('usage','in',('internal','internal'))])
		locat_ids = [elemt.id for elemt in locat_ids]
		res.update({'location_ids':[(6,0,locat_ids)]})
		return res

	@api.onchange('alllocations')
	def onchange_alllocations(self):
		if self.alllocations == True:
			locat_ids = self.env['stock.location'].search( [('usage','in',('internal','internal'))] )
			self.location_ids = [(6,0,locat_ids.ids)]
		else:
			self.location_ids = [(6,0,[])]

	def do_csvtoexcel(self):
		cad = ""

		s_prod = [-1,-1,-1]
		s_loca = [-1,-1,-1]
		if self.alllocations == True:
			locat_ids = self.env['stock.location'].search( [('usage','in',('internal','internal'))] )
			lst_locations = locat_ids.ids
		else:
			lst_locations = self.location_ids.ids
		lst_products  = self.products_ids.ids
		productos='{'
		almacenes='{'
		date_ini=self.fini
		date_fin=self.ffin
		if self.allproducts:
			lst_products = self.env['product.product'].with_context(active_test=False).search([]).ids

		else:
			lst_products = self.products_ids.ids

		if len(lst_products) == 0:
			raise UserError('No existen productos seleccionados')

		for producto in lst_products:
			productos=productos+str(producto)+','
			s_prod.append(producto)
		productos=productos[:-1]+'}'
		for location in lst_locations:
			almacenes=almacenes+str(location)+','
			s_loca.append(location)
		almacenes=almacenes[:-1]+'}'



		config = self.env['kardex.parameter'].search([('company_id','=',self.env.company.id)])

		date_ini = '%d-01-01' % ( config._get_anio_start(date_ini.year) )

		kardex_save_obj = self.env['kardex.save'].search([('company_id','=',self.env.company.id),('state','=','done'),('name.date_end','<',self.fini)]).sorted(lambda l: l.name.code , reverse=True)
		if len(kardex_save_obj)>0:
			kardex_save_obj = kardex_save_obj[0]
			date_ini = kardex_save_obj.name.date_end + timedelta(days=1)
			
		
		si_existe = ""
		if kardex_save_obj:
			si_existe = """ select '"""+str(kardex_save_obj.name.date_end)+"""'::date as fecha,
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

			 and ksp.almacen in  """+str(tuple(s_loca))+"""
			 and ksp.producto in  """+str(tuple(s_prod))+"""
			union all """

		import io
		from xlsxwriter.workbook import Workbook
		output = io.BytesIO()

		#direccion = self.env['main.parameter'].search([])[0].dir_create_file
		workbook = Workbook(output, {'constant_memory': True})
		worksheet = workbook.add_worksheet("Kardex")
		bold = workbook.add_format({'bold': True})
		bold.set_font_size(8)
		normal = workbook.add_format()
		boldbord = workbook.add_format({'bold': True})
		boldbord.set_border(style=2)
		boldbord.set_align('center')
		boldbord.set_align('vcenter')
		boldbord.set_text_wrap()
		boldbord.set_font_size(8)
		boldbord.set_bg_color('#DCE6F1')

		especial1 = workbook.add_format({'bold': True})
		especial1.set_align('center')
		especial1.set_align('vcenter')
		especial1.set_text_wrap()
		especial1.set_font_size(15)

		numbertres = workbook.add_format({'num_format':'0.000'})
		numberdos = workbook.add_format({'num_format':'0.00'})
		numberseis = workbook.add_format({'num_format':'0.000000'})
		numberseis.set_font_size(8)
		numberocho = workbook.add_format({'num_format':'0.00000000'})
		numberocho.set_font_size(8)
		bord = workbook.add_format()
		bord.set_border(style=1)
		bord.set_font_size(8)
		numberdos.set_border(style=1)
		numberdos.set_font_size(8)
		numbertres.set_border(style=1)
		numberseis.set_border(style=1)
		numberocho.set_border(style=1)
		numberdosbold = workbook.add_format({'num_format':'0.00','bold':True})
		numberdosbold.set_font_size(8)
		
		formatdate = workbook.add_format({'num_format': 'dd-mm-yyyy'})
		formatdate.set_border(style=1)
		formattime = workbook.add_format({'num_format': 'HH:mm'})
		formattime.set_border(style=1)
		x= 10
		tam_col = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
		tam_letra = 1.2

		worksheet.merge_range(1,5,1,10, "KARDEX FISICO", especial1)
		worksheet.write(2,0,'FECHA INICIO:',bold)
		worksheet.write(2,1,str(self.fini))
		worksheet.write(3,0,'FECHA FIN:',bold)
		worksheet.write(3,1,str(self.ffin))
		import datetime


		worksheet.write(8,11, "Ingreso",boldbord)
		worksheet.write(8,12, "Salida",boldbord)		
		worksheet.write(8,13, "Saldo",boldbord)

		worksheet.write(9,0, u"Fecha",boldbord)
		worksheet.write(9,1, u"Hora",boldbord)
		worksheet.write(9,2, u"Ubicacion Origen",boldbord)
		worksheet.write(9,3, u"Ubicacion Destino",boldbord)
		worksheet.write(9,4, u"Almacen",boldbord)
		worksheet.write(9,5, u"Tipo de Operación",boldbord)
		worksheet.write(9,6, u"Categoria",boldbord)
		worksheet.write(9,7, u"Producto",boldbord)
		worksheet.write(9,8, u"Codigo P.",boldbord)
		worksheet.write(9,9, u"Unidad",boldbord)
		worksheet.write(9,10, u"Doc. Almacen",boldbord)
		worksheet.write(9,11, "Cantidad",boldbord)
		worksheet.write(9,12, "Cantidad",boldbord)
		worksheet.write(9,13, "Cantidad",boldbord)



		text_report = "<center><b>Cargando Kardex Fisico</b></center><br/><center>Ejecutando SQL del kardex ... Espere por favor</center>"
		self.send_message(text_report)

		self.env.cr.execute("""

		select 
		(vstf.fecha - interval '5' hour)::date as "Fecha",
		(vstf.fecha - interval '5' hour)::time as "Hora",
		origen AS "Ubicación Origen",
		destino AS "Ubicación Destino",
		almacen AS "Almacén",
		vstf.motivo_guia::varchar AS "Tipo de operación",
		categoria as "Categoria",
		producto as "Producto",
		cod_pro as "Codigo P.",
		unidad as "Unidad",
		
		vstf.name as "Doc. Almacén",
		vstf.entrada as "Entrada",
		vstf.salida as "Salida"
		from
		(""" +si_existe+ """
		select vst_kardex_fisico.date as fecha,u_origen as origen, u_destino as destino, u_destino as almacen, vst_kardex_fisico.product_qty as entrada, 0 as salida,vst_kardex_fisico.id  as stock_move,vst_kardex_fisico.guia as motivo_guia, producto,vst_kardex_fisico.estado,vst_kardex_fisico.name, cod_pro, categoria, unidad,product_id,location_dest_id as almacen_id from vst_kardex_fisico_lote() as vst_kardex_fisico where company_id = """+str(self.env.company.id)+"""
		and (date - interval '5' hour)::date >='""" +str(date_ini)+ """' and (date - interval '5' hour)::date <='""" +str(date_fin)+ """'			
		union all
		select vst_kardex_fisico.date as fecha,u_origen as origen, u_destino as destino, u_origen as almacen, 0 as entrada, vst_kardex_fisico.product_qty as salida,vst_kardex_fisico.id  as stock_move ,vst_kardex_fisico.guia as motivo_guia ,producto ,vst_kardex_fisico.estado,vst_kardex_fisico.name, cod_pro, categoria, unidad,product_id, location_id as almacen_id from vst_kardex_fisico_lote() as vst_kardex_fisico where company_id = """+str(self.env.company.id)+"""
		and (date - interval '5' hour)::date >='""" +str(date_ini)+ """' and (date - interval '5' hour)::date <='""" +str(date_fin)+ """'			
		) as vstf
		where vstf.product_id in """ +str(tuple(s_prod))+ """
		and vstf.almacen_id in """ +str(tuple(s_loca))+ """
		and vstf.estado = 'done'
		order by
		almacen,producto,vstf.fecha;


		""")
		total_all = self.env.cr.fetchall()
		ingreso1= 0
		ingreso2= 0
		salida1= 0
		salida2= 0

		saldo = 0
		almacen = None
		producto = None


		self.send_message("Generando Kardex Fisico<br/><center>Total lineas a generar: "+str(len(total_all)) + "</center>")
		cont_report = 0
		import datetime
		tiempo_inicial = datetime.datetime.now()
		tiempo_pasado = [0,0]
		cprom_data = {}


		for line in total_all:
			cont_report += 1
			if cont_report%300 == 0:
				tiempo_pasado = divmod((datetime.datetime.now()-tiempo_inicial).seconds,60)
				text_report = ""
				text_report = "<b>Generando Kardex Fisico.</b><br/><center>Total lineas a procesar: "+str(len(total_all)) + "</center><br/><center>Procesado:"+str(cont_report)+"/"+str(len(total_all))+"</center><br/> Tiempo Procesado: "+ str(tiempo_pasado[0])+" minutos " +str(tiempo_pasado[1]) + " segundos" 
				text_report += """<div id="myProgress" style="position: relative; width: 100%;  height: 30px;   background-color: white;">
				  <div id="myBar" style="position: absolute;  width: """+"%.2f"%(cont_report*100/len(total_all))+"""%;  height: 100%; background-color: #875A7B;">
					<div id="label" style="text-align: center; line-height: 30px; color: white;">""" +"%.2f"%(cont_report*100/len(total_all))+ """%</div>
				  </div>
				</div>"""
				self.send_message(text_report)

			if almacen == None:
				almacen = (line[4] if line[4] else '')
				producto = (line[7] if line[7] else '')
				saldo = line[11] - line[12]
			elif almacen != (line[4] if line[4] else '') or producto != (line[7] if line[7] else ''):
				almacen = (line[4] if line[4] else '')
				producto = (line[7] if line[7] else '')
				saldo = line[11] - line[12]
			else:
				saldo = saldo + line[11] - line[12]

			worksheet.write(x,0,line[0] if line[0] else '' ,formatdate )
			worksheet.write(x,1,line[1] if line[1] else '' ,formattime )
			worksheet.write(x,2,line[2] if line[2] else '' ,bord )
			worksheet.write(x,3,line[3] if line[3] else '' ,bord )
			worksheet.write(x,4,line[4] if line[4] else '' ,bord )
			worksheet.write(x,5,line[5] if line[5] else '' ,bord )
			worksheet.write(x,6,line[6] if line[6] else '' ,bord )
			worksheet.write(x,7,line[7] if line[7] else '' ,bord )
			worksheet.write(x,8,line[8] if line[8] else '' ,bord )
			worksheet.write(x,9,line[9] if line[9] else '' ,bord )
			worksheet.write(x,10,line[10] if line[10] else '' ,bord )
			worksheet.write(x,11,line[11] if line[11] else 0 ,numberdos )
			worksheet.write(x,12,line[12] if line[12] else 0 ,numberdos )
			worksheet.write(x,13,saldo ,numberdos )

			x = x +1

		tam_col = [11,11,5,5,7,5,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11]





		worksheet.set_column('A:A', tam_col[0])
		worksheet.set_column('B:B', tam_col[1])
		worksheet.set_column('C:C', tam_col[2])
		worksheet.set_column('D:D', tam_col[3])
		worksheet.set_column('E:E', tam_col[4])
		worksheet.set_column('F:F', tam_col[5])
		worksheet.set_column('G:G', tam_col[6])
		worksheet.set_column('H:H', tam_col[7])
		worksheet.set_column('I:I', tam_col[8])
		worksheet.set_column('J:J', tam_col[9])
		worksheet.set_column('K:K', tam_col[10])
		worksheet.set_column('L:L', tam_col[11])
		worksheet.set_column('M:M', tam_col[12])
		worksheet.set_column('N:N', tam_col[13])
		worksheet.set_column('O:O', tam_col[14])
		worksheet.set_column('P:P', tam_col[15])
		worksheet.set_column('Q:Q', tam_col[16])
		worksheet.set_column('R:R', tam_col[17])
		worksheet.set_column('S:S', tam_col[18])
		worksheet.set_column('T:Z', tam_col[19])


		workbook.close()
		output.seek(0)

		attach_id = self.env['ir.attachment'].create({
					'name': "Kardex Fisico.xlsx",
					'type': 'binary',
					'datas': base64.encodebytes(output.getvalue()),
					'eliminar_automatico': True
				})
		output.close()

		return {
			'type': 'ir.actions.client',
			'tag': 'notification_llikha',
			'params': {
				'title':'Kardex Fisico Excel',
				'type': 'success',
				'sticky': True,
				'message': 'Se proceso de '+str(self.fini)+' al ' + str(self.ffin)+ '.<br/>Lineas procesadas: '+ str(len(total_all)) +'<br/>Tiempo: ' + str(tiempo_pasado[0])+" minutos " +str(tiempo_pasado[1]) + " segundos",
				'next': {'type': 'ir.actions.act_window_close'},
				'buttons':[{
					'label':'Descargar Kardex Fisico',
					'model':'ir.attachment',
					'method':'get_download_ls',
					'id':attach_id.id,
					}
				],
			}
		}

class make_kardex_product(models.TransientModel):
	_name = "make.kardex.product"
	_description = "make kardex product"

	fini= fields.Date('Fecha inicial',required=True)
	ffin= fields.Date('Fecha final',required=True)
	location_ids=fields.Many2many('stock.location','rel_kardex_location_product','location_id','kardex_id','Ubicacion',required=True)
	destino = fields.Selection([('csv','CSV'),('crt','Pantalla')],'Destino')
	check_fecha = fields.Boolean('Editar Fecha')
	alllocations = fields.Boolean('Todos los almacenes',default=True)

	fecha_ini_mod = fields.Date('Fecha Inicial')
	fecha_fin_mod = fields.Date('Fecha Final')
	analizador = fields.Boolean('Analizador')

	@api.onchange('fecha_ini_mod')
	def onchange_fecha_ini_mod(self):
		self.fini = self.fecha_ini_mod


	@api.onchange('fecha_fin_mod')
	def onchange_fecha_fin_mod(self):
		self.ffin = self.fecha_fin_mod


	@api.model
	def default_get(self, fields):
		res = super(make_kardex_product, self).default_get(fields)
		import datetime
		fecha_hoy = str(datetime.datetime.now())[:10]
		fecha_inicial = fecha_hoy[:4] + '-01-01'
		res.update({'fecha_ini_mod':fecha_inicial})
		res.update({'fecha_fin_mod':fecha_hoy})
		res.update({'fini':fecha_inicial})
		res.update({'ffin':fecha_hoy})

		#locat_ids = self.pool.get('stock.location').search(cr, uid, [('usage','in',('internal','inventory','transit','procurement','production'))])
		locat_ids = self.env['stock.location'].search([('usage','in',('internal','inventory','transit','procurement','production'))])
		locat_ids = [elemt.id for elemt in locat_ids]
		res.update({'location_ids':[(6,0,locat_ids)]})
		return res

	@api.onchange('alllocations')
	def onchange_alllocations(self):
		if self.alllocations == True:
			locat_ids = self.env['stock.location'].search( [('usage','in',('internal','internal'))] )
			self.location_ids = [(6,0,locat_ids.ids)]
		else:
			self.location_ids = [(6,0,[])]



	def do_csvtoexcel(self):
		fields = {
			'fini':self.fini,
			'ffin':self.ffin,
			'products_ids':[(6,0,[self.env.context['active_id']])],
			'location_ids':[(6,0,self.location_ids)],
			'allproducts':self.allproducts,
			'destino':False,
			'check_fecha':self.check_fecha,
			'alllocations':self.alllocations,
			'fecha_ini_mod':self.fecha_ini_mod,
			'fecha_fin_mod':self.fecha_fin_mod,
			'analizador':self.analizador,
		}
		wizard_original = self.env['make.kardex'].create(fields)
		return wizard_original.do_csvtoexcel()





		
class make_kardex_lote(models.TransientModel):
	_name = "make.kardex.lote"
	_description = "make kardex lote"

	fini= fields.Date('Fecha inicial',required=True)
	ffin= fields.Date('Fecha final',required=True)
	products_ids=fields.Many2many('product.product','rel_wiz_kardex_lote','product_id','kardex_id')
	location_ids=fields.Many2many('stock.location','rel_kardex_location_lote','location_id','kardex_id','Ubicacion',required=True)
	allproducts=fields.Boolean('Todos los productos',default=True)
	destino = fields.Selection([('csv','CSV'),('crt','Pantalla')],'Destino')
	check_fecha = fields.Boolean('Editar Fecha')
	alllocations = fields.Boolean('Todos los almacenes',default=True)
	fecha_ini_mod = fields.Date('Fecha Inicial')
	fecha_fin_mod = fields.Date('Fecha Final')
	analizador = fields.Boolean('Analizador')

	@api.onchange('fecha_ini_mod')
	def onchange_fecha_ini_mod(self):
		self.fini = self.fecha_ini_mod

	@api.onchange('fecha_fin_mod')
	def onchange_fecha_fin_mod(self):
		self.ffin = self.fecha_fin_mod

	@api.model
	def default_get(self, fields):
		res = super(make_kardex_lote, self).default_get(fields)
		import datetime
		fecha_hoy = str(datetime.datetime.now())[:10]
		fecha_inicial = fecha_hoy[:4] + '-01-01'
		res.update({'fecha_ini_mod':fecha_inicial})
		res.update({'fecha_fin_mod':fecha_hoy})
		res.update({'fini':fecha_inicial})
		res.update({'ffin':fecha_hoy})
		#locat_ids = self.pool.get('stock.location').search(cr, uid, [('usage','in',('internal','inventory','transit','procurement','production'))])
		locat_ids = self.env['stock.location'].search([('usage','in',('internal','internal'))])
		locat_ids = [elemt.id for elemt in locat_ids]
		res.update({'location_ids':[(6,0,locat_ids)]})
		return res

	@api.onchange('alllocations')
	def onchange_alllocations(self):
		if self.alllocations == True:
			locat_ids = self.env['stock.location'].search( [('usage','in',('internal','internal'))] )
			self.location_ids = [(6,0,locat_ids.ids)]
		else:
			self.location_ids = [(6,0,[])]

	def do_csvtoexcel(self):
		
		cad = ""

		s_prod = [-1,-1,-1]
		s_loca = [-1,-1,-1]
		if self.alllocations == True:
			locat_ids = self.env['stock.location'].search( [('usage','in',('internal','internal'))] )
			lst_locations = locat_ids.ids
		else:
			lst_locations = self.location_ids.ids
		lst_products  = self.products_ids.ids
		productos='{'
		almacenes='{'
		date_ini=self.fini
		date_fin=self.ffin
		if self.allproducts:
			lst_products = self.env['product.product'].with_context(active_test=False).search([]).ids

		else:
			lst_products = self.products_ids.ids

		if len(lst_products) == 0:
			raise UserError('No existen productos seleccionados')

		for producto in lst_products:
			productos=productos+str(producto)+','
			s_prod.append(producto)
		productos=productos[:-1]+'}'
		for location in lst_locations:
			almacenes=almacenes+str(location)+','
			s_loca.append(location)
		almacenes=almacenes[:-1]+'}'


		config = self.env['kardex.parameter'].search([('company_id','=',self.env.company.id)])

		date_ini = '%d-01-01' % ( config._get_anio_start(date_ini.year) )

		kardex_save_obj = self.env['kardex.save'].search([('company_id','=',self.env.company.id),('state','=','done'),('name.date_end','<',self.fini),('name.fiscal_year_id.name','=',str(date_fin.year) )]).sorted(lambda l: l.name.code , reverse=True)
		if len(kardex_save_obj)>0:
			kardex_save_obj = kardex_save_obj[0]
			date_ini = kardex_save_obj.name.date_end + timedelta(days=1)
			
		
		si_existe = ""
		if kardex_save_obj:
			si_existe = """ select '"""+str(kardex_save_obj.name.date_end)+"""'::date as fecha,
			'SALDO INICIAL' as origen, sl.complete_name as destino, sl.complete_name as almacen, ksp.stock as entrada, 0 as salida, null as stock_move,
			'' as motivo_guia, pname.new_name as producto, 'done' as estado, 'Saldo Inicial' as name, coalesce(pp.default_code,pt.default_code) as cod_pro,
			pc.name as categoria, uu.name as unidad, ksp.producto as product_id, ksp.almacen as almacen_id, spt.name as lote
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
			 
			 and ksp.almacen in  """+str(tuple(s_loca))+"""
			 and ksp.producto in  """+str(tuple(s_prod))+"""
			union all """


		import io
		from xlsxwriter.workbook import Workbook
		output = io.BytesIO()

		#direccion = self.env['main.parameter'].search([])[0].dir_create_file
		workbook = Workbook(output, {'constant_memory': True})
		worksheet = workbook.add_worksheet("Kardex")
		bold = workbook.add_format({'bold': True})
		bold.set_font_size(8)
		normal = workbook.add_format()
		boldbord = workbook.add_format({'bold': True})
		boldbord.set_border(style=2)
		boldbord.set_align('center')
		boldbord.set_align('vcenter')
		boldbord.set_text_wrap()
		boldbord.set_font_size(8)
		boldbord.set_bg_color('#DCE6F1')

		especial1 = workbook.add_format({'bold': True})
		especial1.set_align('center')
		especial1.set_align('vcenter')
		especial1.set_text_wrap()
		especial1.set_font_size(15)

		numbertres = workbook.add_format({'num_format':'0.000'})
		numberdos = workbook.add_format({'num_format':'0.00'})
		numberseis = workbook.add_format({'num_format':'0.000000'})
		numberseis.set_font_size(8)
		numberocho = workbook.add_format({'num_format':'0.00000000'})
		numberocho.set_font_size(8)
		bord = workbook.add_format()
		bord.set_border(style=1)
		bord.set_font_size(8)
		numberdos.set_border(style=1)
		numberdos.set_font_size(8)
		numbertres.set_border(style=1)
		numberseis.set_border(style=1)
		numberocho.set_border(style=1)
		numberdosbold = workbook.add_format({'num_format':'0.00','bold':True})
		numberdosbold.set_font_size(8)
		
		formatdate = workbook.add_format({'num_format': 'dd-mm-yyyy'})
		formattime = workbook.add_format({'num_format': 'HH:mm'})
		x= 10
		tam_col = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
		tam_letra = 1.2

		worksheet.merge_range(1,5,1,10, "KARDEX FISICO", especial1)
		worksheet.write(2,0,'FECHA INICIO:',bold)
		worksheet.write(3,0,'FECHA FIN:',bold)

		worksheet.write(2,1,str(self.fini))
		worksheet.write(3,1,str(self.ffin))
		import datetime

		worksheet.write(8,12, "Ingreso",boldbord)
		worksheet.write(8,13, "Salida",boldbord)		
		worksheet.write(8,14, "Saldo",boldbord)

		worksheet.write(9,0, u"Fecha",boldbord)
		worksheet.write(9,1, u"Hora",boldbord)
		worksheet.write(9,2, u"Ubicacion Origen",boldbord)
		worksheet.write(9,3, u"Ubicacion Destino",boldbord)
		worksheet.write(9,4, u"Almacen",boldbord)
		worksheet.write(9,5, u"Tipo de Operación",boldbord)
		worksheet.write(9,6, u"Categoria",boldbord)
		worksheet.write(9,7, u"Producto",boldbord)
		worksheet.write(9,8, u"Codigo P.",boldbord)
		worksheet.write(9,9, u"Lote",boldbord)
		worksheet.write(9,10, u"Unidad",boldbord)
		worksheet.write(9,11, u"Doc. Almacen",boldbord)
		worksheet.write(9,12, "Cantidad",boldbord)
		worksheet.write(9,13, "Cantidad",boldbord)
		worksheet.write(9,14, "Cantidad",boldbord)
		worksheet.write(9,15, "Cliente",boldbord)
		worksheet.write(9,16, "Nro Factura",boldbord)




		self.env.cr.execute("""

select 
(vstf.fecha - interval '5' hour)::date as "Fecha",
(vstf.fecha - interval '5' hour) ::time as "Hora",
origen AS "Ubicación Origen",
destino AS "Ubicación Destino",
almacen AS "Almacén",
vstf.motivo_guia::varchar AS "Tipo de operación",
categoria as "Categoria",
producto as "Producto",
cod_pro as "Codigo P.",
vstf.lote as "Lote",

unidad as "unidad",

vstf.name as "Doc. Almacén",
vstf.entrada as "Entrada",
vstf.salida as "Salida",
rp.name as partner,
am.ref as comprobante
--sp.numberg as guia

from
(""" +si_existe+ """	
select vst_kardex_fisico.date as fecha,u_origen as origen, u_destino as destino, u_destino as almacen, vst_kardex_fisico.product_qty as entrada, 0 as salida,vst_kardex_fisico.id  as stock_move,vst_kardex_fisico.guia as motivo_guia, producto,vst_kardex_fisico.estado,vst_kardex_fisico.name, cod_pro, categoria, unidad,product_id,location_dest_id as almacen_id,lote from vst_kardex_fisico_lote() as vst_kardex_fisico where company_id = """+str(self.env.company.id)+"""
and (date - interval '5' hour)::date >='""" +str(date_ini)+ """' and (date - interval '5' hour)::date <='""" +str(date_fin)+ """'			
union all
select vst_kardex_fisico.date as fecha,u_origen as origen, u_destino as destino, u_origen as almacen, 0 as entrada, vst_kardex_fisico.product_qty as salida,vst_kardex_fisico.id  as stock_move ,vst_kardex_fisico.guia as motivo_guia ,producto ,vst_kardex_fisico.estado,vst_kardex_fisico.name, cod_pro, categoria, unidad,product_id, location_id as almacen_id , lote from vst_kardex_fisico_lote() as vst_kardex_fisico where company_id = """+str(self.env.company.id)+"""
and (date - interval '5' hour)::date >='""" +str(date_ini)+ """' and (date - interval '5' hour)::date <='""" +str(date_fin)+ """'			
) as vstf
left join stock_move sm on sm.id = vstf.stock_move
left join stock_picking sp on sp.id = sm.picking_id
left join res_partner rp on rp.id =  sp.partner_id
left join account_move am on am.id = sm.invoice_id
where 
vstf.product_id in """ +str(tuple(s_prod))+ """
and vstf.almacen_id in """ +str(tuple(s_loca))+ """
and vstf.estado = 'done'
order by
almacen,producto,lote,vstf.fecha;


		""")

		ingreso1= 0
		ingreso2= 0
		salida1= 0
		salida2= 0

		saldo = 0
		almacen = None
		producto = None
		lote = None

		tiempo_inicial = datetime.datetime.now()
		tiempo_pasado = [0,0]
		cont_report = 0

		total_all = self.env.cr.fetchall()
		for line in total_all:
			cont_report += 1
			if cont_report%300 == 0:
				tiempo_pasado = divmod((datetime.datetime.now()-tiempo_inicial).seconds,60)
				text_report = ""
				text_report = "<b>Generando Kardex Fisico x Lote.</b><br/><center>Total lineas a procesar: "+str(len(total_all)) + "</center><br/><center>Procesado:"+str(cont_report)+"/"+str(len(total_all))+"</center><br/> Tiempo Procesado: "+ str(tiempo_pasado[0])+" minutos " +str(tiempo_pasado[1]) + " segundos" 
				text_report += """<div id="myProgress" style="position: relative; width: 100%;  height: 30px;   background-color: white;">
				  <div id="myBar" style="position: absolute;  width: """+"%.2f"%(cont_report*100/len(total_all))+"""%;  height: 100%; background-color: #875A7B;">
					<div id="label" style="text-align: center; line-height: 30px; color: white;">""" +"%.2f"%(cont_report*100/len(total_all))+ """%</div>
				  </div>
				</div>"""
				self.send_message(text_report)

			if almacen == None:
				almacen = (line[4] if line[4] else '')
				producto = (line[7] if line[7] else '')
				lote = (line[9] if line[9] else '')
				saldo = line[12] - line[13]
			elif almacen != (line[4] if line[4] else '') or producto != (line[7] if line[7] else '') or lote != (line[9] if line[9] else ''):
				almacen = (line[4] if line[4] else '')
				producto = (line[7] if line[7] else '')
				lote = (line[9] if line[9] else '')
				saldo = line[12] - line[13]
			else:
				saldo = saldo + line[12] - line[13]

			worksheet.write(x,0,line[0] if line[0] else '' ,formatdate )
			worksheet.write(x,1,line[1] if line[1] else '' ,formattime )
			worksheet.write(x,2,line[2] if line[2] else '' ,bord )
			worksheet.write(x,3,line[3] if line[3] else '' ,bord )
			worksheet.write(x,4,line[4] if line[4] else '' ,bord )
			worksheet.write(x,5,line[5] if line[5] else '' ,bord )
			worksheet.write(x,6,line[6] if line[6] else '' ,bord )
			worksheet.write(x,7,line[7] if line[7] else '' ,bord )
			worksheet.write(x,8,line[8] if line[8] else '' ,bord )
			worksheet.write(x,9,line[9] if line[9] else '' ,bord)
			worksheet.write(x,10,line[10] if line[10] else '' ,bord )
			worksheet.write(x,11,line[11] if line[11] else 0 ,numberdos )
			worksheet.write(x,12,line[12] if line[12] else 0 ,numberdos )
			worksheet.write(x,13,line[13] if line[13] else 0 ,numberdos )
			worksheet.write(x,14,saldo ,numberdos )
			worksheet.write(x,15,line[14] if line[14] else '' ,bord )
			#worksheet.write(x,16,line[16] if line[16] else '' ,bord )
			worksheet.write(x,16,line[15] if line[15] else '' ,bord )


			x = x +1

		tam_col = [11,11,5,5,7,5,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11]


		worksheet.set_column('A:A', tam_col[0])
		worksheet.set_column('B:B', tam_col[1])
		worksheet.set_column('C:C', tam_col[2])
		worksheet.set_column('D:D', tam_col[3])
		worksheet.set_column('E:E', tam_col[4])
		worksheet.set_column('F:F', tam_col[5])
		worksheet.set_column('G:G', tam_col[6])
		worksheet.set_column('H:H', tam_col[7])
		worksheet.set_column('I:I', tam_col[8])
		worksheet.set_column('J:J', tam_col[9])
		worksheet.set_column('K:K', tam_col[10])
		worksheet.set_column('L:L', tam_col[11])
		worksheet.set_column('M:M', tam_col[12])
		worksheet.set_column('N:N', tam_col[13])
		worksheet.set_column('O:O', tam_col[14])
		worksheet.set_column('P:P', tam_col[15])
		worksheet.set_column('Q:Q', tam_col[16])
		worksheet.set_column('R:R', tam_col[17])
		worksheet.set_column('S:S', tam_col[18])
		worksheet.set_column('T:Z', tam_col[19])


		workbook.close()
		output.seek(0)

		attach_id = self.env['ir.attachment'].create({
					'name': "Kardex Fisico.xlsx",
					'type': 'binary',
					'datas': base64.encodebytes(output.getvalue()),
					'eliminar_automatico': True
				})
		output.close()
		
		return {
			'type': 'ir.actions.client',
			'tag': 'notification_llikha',
			'params': {
				'title':'Kardex Fisico x Lote Excel',
				'type': 'success',
				'sticky': True,
				'message': 'Se proceso de '+str(self.fini)+' al ' + str(self.ffin)+ '.<br/>Lineas procesadas: '+ str(len(total_all)) +'<br/>Tiempo: ' + str(tiempo_pasado[0])+" minutos " +str(tiempo_pasado[1]) + " segundos",
				'next': {'type': 'ir.actions.act_window_close'},
				'buttons':[{
					'label':'Descargar Kardex Fisico x Lote',
					'model':'ir.attachment',
					'method':'get_download_ls',
					'id':attach_id.id,
					}
				],
			}
		}