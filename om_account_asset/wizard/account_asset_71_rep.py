# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError
import base64

from lxml import etree
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, inch, landscape
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.lib.utils import simpleSplit
from reportlab.pdfgen import canvas
import decimal

class AccountAsset71Rep(models.TransientModel):
	_name = 'account.asset.71.rep'
	_description = 'Account Asset 71 Rep'

	name = fields.Char()
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company)
	fiscal_year_id = fields.Many2one('account.fiscal.year',string=u'Año Fiscal',required=True)
	period = fields.Many2one('account.period',string='Periodo',required=True)
	type_show =  fields.Selection([('pantalla','Pantalla'),('excel','Excel'),('pdf','PDF')],string=u'Mostrar en',default='pantalla')
	
	@api.onchange('company_id')
	def get_fiscal_year(self):
		if self.company_id:
			today = fields.Date.context_today(self)
			fiscal_year = self.env['account.fiscal.year'].search([('name','=',str(today.year))],limit=1)
			if fiscal_year:
				self.fiscal_year_id = fiscal_year.id

	def get_report(self):
		self.env.cr.execute("""
				CREATE OR REPLACE view account_asset_71_book as ("""+self._get_sql_71(self.fiscal_year_id.date_from,self.period.date_start,self.period.date_end,self.company_id.id,self.period.code)+""")""")
				
		if self.type_show == 'pantalla':
			return {
				'name': 'Formato 7.1',
				'type': 'ir.actions.act_window',
				'res_model': 'account.asset.71.book',
				'view_mode': 'tree',
				'view_type': 'form',
				'views': [(False, 'tree')],
			}

		if self.type_show == 'excel':
			return self.get_excel()
		
		if self.type_show == 'pdf':
			return self.getPdf()

	def get_excel(self):
		import io
		from xlsxwriter.workbook import Workbook

		ReportBase = self.env['report.base']
		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'Formato_71.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		##########FORMATO 7.1############
		worksheet = workbook.add_worksheet("FORMATO 7.1")
		worksheet.set_tab_color('blue')
		
		worksheet.merge_range(0,0,1,0, u"Código Relacionado con el Activo Fijo",formats['boldbord'])
		worksheet.merge_range(0,1,1,1, "Cuenta Contable del Activo Fijo",formats['boldbord'])
		worksheet.merge_range(0,2,0,5, u"Detalle del Activo Fijo",formats['boldbord'])
		HEADERS = [u'Descripción',u'Marca del Activo Fijo',u'Modelo del Activo Fijo',u'Número de Serie y/o Placa del Activo Fijo']
		worksheet = ReportBase.get_headers(worksheet,HEADERS,1,2,formats['boldbord'])
		worksheet.merge_range(0,6,1,6, "Saldo Inicial",formats['boldbord'])
		worksheet.merge_range(0,7,1,7, "Adquisiones Adiciones",formats['boldbord'])
		worksheet.merge_range(0,8,1,8, "Mejoras",formats['boldbord'])
		worksheet.merge_range(0,9,1,9, "Retiros y/o Bajas",formats['boldbord'])
		worksheet.merge_range(0,10,1,10, "Otros Ajustes",formats['boldbord'])
		worksheet.merge_range(0,11,1,11, u"Valor Histórico del Activo Fijo al 31.12",formats['boldbord'])
		worksheet.merge_range(0,12,1,12, u"Ajuste por Inflación",formats['boldbord'])
		worksheet.merge_range(0,13,1,13, "Valor Ajustado del Activo Fijo al 31.12",formats['boldbord'])
		worksheet.merge_range(0,14,1,14, u"Fecha de Adquisición",formats['boldbord'])
		worksheet.merge_range(0,15,1,15, "Fecha Inicio del Uso del Activo Fijo",formats['boldbord'])
		worksheet.merge_range(0,16,0,17, u"Depreciación",formats['boldbord'])
		HEADERS = [u'Método Aplicado',u'Nro de Documento de Autorización']
		worksheet = ReportBase.get_headers(worksheet,HEADERS,1,16,formats['boldbord'])
		worksheet.merge_range(0,18,1,18, u"Porcentaje de Depreciación",formats['boldbord'])
		worksheet.merge_range(0,19,1,19, u"Depreciación acumulada al Cierre del Ejercicio Anterior",formats['boldbord'])
		worksheet.merge_range(0,20,1,20, u"Depreciación del Ejercicio",formats['boldbord'])
		worksheet.merge_range(0,21,1,21, u"Depreciación del Ejercicio Relacionada con los retiros y/o bajas",formats['boldbord'])
		worksheet.merge_range(0,22,1,22, u"Depreciación relacionada con otros ajustes",formats['boldbord'])
		worksheet.merge_range(0,23,1,23, u"Depreciación acumulada Histórico",formats['boldbord'])
		worksheet.merge_range(0,24,1,24, u"Ajuste por inflación de la Depreciación",formats['boldbord'])
		worksheet.merge_range(0,25,1,25, u"Depreciación acumulada Ajustada por Inflación",formats['boldbord'])
		x=2

		for line in self.env['account.asset.71.book'].search([]):
			worksheet.write(x,0,line.campo1 if line.campo1 else '',formats['especial1'])
			worksheet.write(x,1,line.campo2 if line.campo2 else '',formats['especial1'])
			worksheet.write(x,2,line.campo3 if line.campo3 else '',formats['especial1'])
			worksheet.write(x,3,line.campo4 if line.campo4 else '',formats['especial1'])
			worksheet.write(x,4,line.campo5 if line.campo5 else '',formats['especial1'])
			worksheet.write(x,5,line.campo6 if line.campo6 else '',formats['especial1'])
			worksheet.write(x,6,line.campo7 if line.campo7 else '0.00',formats['numberdos'])
			worksheet.write(x,7,line.campo8 if line.campo8 else '0.00',formats['numberdos'])
			worksheet.write(x,8,line.campo9 if line.campo9 else '0.00',formats['numberdos'])
			worksheet.write(x,9,line.campo10 if line.campo10 else '0.00',formats['numberdos'])
			worksheet.write(x,10,line.campo11 if line.campo11 else '0.00',formats['numberdos'])
			worksheet.write(x,11,line.campo12 if line.campo12 else '0.00',formats['numberdos'])
			worksheet.write(x,12,line.campo13 if line.campo13 else '0.00',formats['numberdos'])
			worksheet.write(x,13,line.campo14 if line.campo14 else '0.00',formats['numberdos'])
			worksheet.write(x,14,line.campo15 if line.campo15 else '',formats['dateformat'])
			worksheet.write(x,15,line.campo16 if line.campo16 else '',formats['dateformat'])
			worksheet.write(x,16,line.campo17 if line.campo17 else '',formats['especial1'])
			worksheet.write(x,17,line.campo18 if line.campo18 else '',formats['especial1'])
			worksheet.write(x,18,line.campo19 if line.campo19 else '0.00',formats['numberdos'])
			worksheet.write(x,19,line.campo20 if line.campo20 else '0.00',formats['numberdos'])
			worksheet.write(x,20,line.campo21 if line.campo21 else '0.00',formats['numberdos'])
			worksheet.write(x,21,line.campo22 if line.campo22 else '0.00',formats['numberdos'])
			worksheet.write(x,22,line.campo23 if line.campo23 else '0.00',formats['numberdos'])
			worksheet.write(x,23,line.campo24 if line.campo24 else '0.00',formats['numberdos'])
			worksheet.write(x,24,line.campo25 if line.campo25 else '0.00',formats['numberdos'])
			worksheet.write(x,25,line.campo26 if line.campo26 else '0.00',formats['numberdos'])
			
			x += 1

		widths = [14,14,55,25,15,14,13,13,13,13,13,13,13,13,12,12,14,17,20,18,13,18,13,13,13,13]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()

		f = open(direccion +'Formato_71.xlsx', 'rb')

		return self.env['popup.it'].get_file('Libro de Activos Formato 71.xlsx',base64.encodebytes(b''.join(f.readlines())))

	def getPdf(self):
		import importlib
		import sys
		importlib.reload(sys)

		
		def particionar_text(c,tam):
			tet = ""
			for i in range(len(c)):
				tet += c[i]
				lines = simpleSplit(tet,'Helvetica',8,tam)
				if len(lines)>1:
					return tet[:-1]
			return tet

		def pdf_header(self,c,wReal,hReal,size_widths):
			
			c.setFont("Helvetica", 10)
			style = getSampleStyleSheet()["Normal"]
			style.leading = 8
			style.alignment= 1

			data= [[Paragraph("<font size=5><b>Código Relacionado con el Activo Fijo</b></font>",style),
				Paragraph("<font size=5><b>Cuenta Contable del Activo Fijo</b></font>",style),
				Paragraph("<font size=5><b>Detalle del Activo Fijo</b></font>",style),'','','',
				Paragraph("<font size=5><b>Saldo Inicial</b></font>",style),
				Paragraph("<font size=5><b>Adquisiones Adiciones</b></font>",style),
				Paragraph("<font size=5><b>Mejoras</b></font>",style),
				Paragraph("<font size=5><b>Retiros y/o Bajas</b></font>",style),
				Paragraph("<font size=5><b>Otros Ajustes</b></font>",style),
				Paragraph("<font size=5><b>Valor Histórico del Activo Fijo al 31.12</b></font>",style),
				Paragraph("<font size=5><b>Ajuste por Inflación</b></font>",style),
				Paragraph("<font size=5><b>Valor Ajustado del Activo Fijo al 31.12</b></font>",style),
				Paragraph("<font size=5><b>Fecha de Adquisición</b></font>",style),
				Paragraph("<font size=5><b>Fecha Inicio del Uso del Activo Fijo</b></font>",style),
				Paragraph("<font size=5><b>Depreciación</b></font>",style),'',
				Paragraph("<font size=5><b>Porcentaje de Depreciación</b></font>",style),
				Paragraph("<font size=5><b>Depreciación acumulada al Cierre del Ejercicio Anterior</b></font>",style),
				Paragraph("<font size=5><b>Depreciación del Ejercicio</b></font>",style),
				Paragraph("<font size=5><b>Depreciación del Ejercicio Relacionada con los retiros y/o bajas</b></font>",style),
				Paragraph("<font size=5><b>Depreciación relacionada con otros ajustes</b></font>",style),
				Paragraph("<font size=5><b>Depreciación acumulada Histórico</b></font>",style),
				Paragraph("<font size=5><b>Ajuste por inflación de la Depreciación</b></font>",style),
				Paragraph("<font size=5><b>Depreciación acumulada Ajustada por Inflación</b></font>",style),],

				['',
				'',
				Paragraph("<font size=5><b>Descripción</b></font>",style),
				Paragraph("<font size=5><b>Marca del Activo Fijo</b></font>",style),
				Paragraph("<font size=5><b>Modelo del Activo Fijo</b></font>",style),
				Paragraph("<font size=5><b>Número de Serie y/o Placa del Activo Fijo</b></font>",style),
				'',
				'',
				'',
				'',
				'',
				'',
				'',
				'',
				'',
				'',
				Paragraph("<font size=5><b>Método Aplicado</b></font>",style),
				Paragraph("<font size=5><b>Nro de Documento de Autorización</b></font>",style),
				'',
				'',
				'',
				'',
				'',
				'',
				'',
				''
				]]
			#
			t=Table(data,colWidths=size_widths, rowHeights=[30,35])
			t.setStyle(TableStyle([
				('SPAN',(0,-2),(0,-1)),						
				('SPAN',(1,-1),(1,0)),
				('SPAN', (2, 0), (5, 0)),
				('SPAN', (6, 0), (6, 1)),
				('SPAN', (7, 0), (7, 1)),
				('SPAN', (8, 0), (8, 1)),
				('SPAN', (9, 0), (9, 1)),
				('SPAN', (10, 0), (10, 1)),
				('SPAN', (11, 0), (11, 1)),
				('SPAN', (12, 0), (12, 1)),
				('SPAN', (13, 0), (13, 1)),
				('SPAN', (14, 0), (14, 1)),
				('SPAN', (15, 0), (15, 1)),
				('SPAN', (16, 0), (17, 0)),
				('SPAN', (18, 0), (18, 1)),
				('SPAN', (19, 0), (19, 1)),
				('SPAN', (20, 0), (20, 1)),
				('SPAN', (21, 0), (21, 1)),
				('SPAN', (22, 0), (22, 1)),
				('SPAN', (23, 0), (23, 1)),
				('SPAN', (24, 0), (24, 1)),
				('SPAN', (25, 0), (25, 1)),
				#('SPAN', (26, 0), (26, 1)),
				('GRID',(0,0),(-1,-1), 1.5, colors.black),
				('ALIGN',(0,0),(-1,-1),'CENTER'),
				('VALIGN',(0,0),(-1,-1),'MIDDLE'),
				('TEXTFONT', (0, 0), (-1, -1), 'Calibri'),
				('LEFTPADDING', (0,0), (-1,-1), 0),
				('RIGHTPADDING', (0,0), (-1,-1), 0),
				('BOTTOMPADDING', (0,0), (-1,-1), 0),
				('TOPPADDING', (0,0), (-1,-1), 0),
				('BACKGROUND', (0, 0), (-1, -1), '#DCE6F1'),
				('FONTSIZE',(0,0),(-1,-1),2)
			]))
			t.wrapOn(c, wReal - 60, hReal - 60) 
			t.drawOn(c,30,hReal-44)
		
		def verify_linea_s(self,c,wReal,hReal,posactual,valor,pagina,size_widths):
			if posactual <50:
				c.showPage()
				pdf_header(self,c,wReal,hReal,size_widths)
				return pagina+1,hReal-60
			else:
				return pagina,posactual-valor
			
		def verify_linea(self,c,wReal,hReal,posactual,valor,pagina,size_widths,totales_hv):
			if posactual <50:
				first_pos_totals = 30
				c.setFont("Helvetica-Bold", 6)
				c.drawString(first_pos_totals +2, pos_inicial-10,"TOTALES")
				first_pos_totals += size_widths[1]+size_widths[2]+size_widths[3]+size_widths[4]+size_widths[5]
				
				c.drawRightString(first_pos_totals + 87, pos_inicial -10, '{:,.2f}'.format((totales_hv['campo7'] if totales_hv['campo7']!=0 else 0.0)))
				first_pos_totals += size_widths[6]
			
				c.drawRightString(first_pos_totals + 87, pos_inicial -10, '{:,.2f}'.format((totales_hv['campo8'] if totales_hv['campo8']!=0 else 0.0))) 
				first_pos_totals += size_widths[7]

				c.drawRightString(first_pos_totals + 87, pos_inicial -10, '{:,.2f}'.format((totales_hv['campo9'] if totales_hv['campo9']!=0 else 0.0))) 
				first_pos_totals += size_widths[8]

				c.drawRightString(first_pos_totals + 87, pos_inicial -10, '{:,.2f}'.format((totales_hv['campo10'] if totales_hv['campo10']!=0 else 0.0))) 
				first_pos_totals += size_widths[9]
					
				c.drawRightString(first_pos_totals + 87, pos_inicial -10, '{:,.2f}'.format((totales_hv['campo11'] if totales_hv['campo11']!=0 else 0.0))) 
				first_pos_totals += size_widths[10]

				c.drawRightString(first_pos_totals + 87, pos_inicial -10, '{:,.2f}'.format((totales_hv['campo12'] if totales_hv['campo12']!=0 else 0.0) ))
				first_pos_totals += size_widths[11]

				c.drawRightString(first_pos_totals + 87, pos_inicial -10, '{:,.2f}'.format((totales_hv['campo13'] if totales_hv['campo13']!=0 else 0.0) ))
				first_pos_totals += size_widths[12]

				c.drawRightString(first_pos_totals + 87, pos_inicial -10, '{:,.2f}'.format((totales_hv['campo14'] if totales_hv['campo14']!=0 else 0.0)) )
				first_pos_totals += size_widths[13]+size_widths[14]+size_widths[15]+size_widths[16] 
					
				c.drawRightString(first_pos_totals + 87, pos_inicial -10, '{:,.2f}'.format((totales_hv['campo18'] if totales_hv['campo18']!=0 else 0.0)) )
				first_pos_totals += size_widths[17]

				c.drawRightString( first_pos_totals + 87 ,pos_inicial -10,( '{:,.2f}'.format((totales_hv['campo19'] if totales_hv['campo19']!=0 else 0.0) )))
				first_pos_totals += size_widths[18]

				c.drawRightString(first_pos_totals + 87, pos_inicial -10, '{:,.2f}'.format((totales_hv['campo20'] if totales_hv['campo20']!=0 else 0.0))) 
				first_pos_totals += size_widths[19]

				c.drawRightString(first_pos_totals + 87 ,pos_inicial -10,( '{:,.2f}'.format((totales_hv['campo21'] if totales_hv['campo21']!=0 else 0.0)) ))
				first_pos_totals += size_widths[20]

				c.drawRightString(first_pos_totals + 87, pos_inicial -10, '{:,.2f}'.format((totales_hv['campo22'] if totales_hv['campo22']!=0 else 0.0))) 
				first_pos_totals += size_widths[21]

				c.drawRightString(first_pos_totals +  87, pos_inicial -10, '{:,.2f}'.format((totales_hv['campo23'] if totales_hv['campo23']!=0 else 0.0))) 
				first_pos_totals += size_widths[22]

				c.drawRightString(first_pos_totals +  87 ,pos_inicial -10,( '{:,.2f}'.format((totales_hv['campo24'] if totales_hv['campo24']!=0 else 0.0)) ))
				first_pos_totals += size_widths[23]

				c.drawRightString(first_pos_totals +  87, pos_inicial -10, '{:,.2f}'.format((totales_hv['campo25'] if totales_hv['campo25']!=0 else 0.0))) 
				first_pos_totals += size_widths[24]

				c.drawRightString(first_pos_totals +  87 ,pos_inicial -10,( '{:,.2f}'.format((totales_hv['campo26'] if totales_hv['campo26']!=0 else 0.0)) ))
				first_pos_totals += size_widths[25]

				c.showPage()
				pdf_header(self,c,wReal,hReal,size_widths)
				return pagina+1,hReal-60
			else:
				return pagina,posactual-valor

		width, height = 1224, 792
		wReal = width - 15
		hReal = height - 40


		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file
		name_file = "formato_1_7.pdf"
		c = canvas.Canvas( direccion + name_file, pagesize=(1224, 792) )
		pos_inicial = hReal-60
		pagina = 1

		size_widths = [45,45,68,43,43,43,44,44,44,44,44,44,44,44,45,45,45,44,44,44,44,44,44,44,44,44] #770

		pdf_header(self,c,wReal,hReal,size_widths)

		c.setFont("Helvetica", 7)

		totales = {
				'campo7': 0,
				'campo8': 0,
				'campo9': 0,
				'campo10': 0,
				'campo11': 0,
				'campo12': 0,
				'campo13': 0,
				'campo14': 0,
				'campo18': 0,
				'campo19': 0,
				'campo20': 0,
				'campo21': 0,
				'campo22': 0,
				'campo23': 0,
				'campo24': 0,
				'campo25': 0,
				'campo26': 0
			}		
		totales_h = {
				'campo7': 0,
				'campo8': 0,
				'campo9': 0,
				'campo10': 0,
				'campo11': 0,
				'campo12': 0,
				'campo13': 0,
				'campo14': 0,
				'campo18': 0,
				'campo19': 0,
				'campo20': 0,
				'campo21': 0,
				'campo22': 0,
				'campo23': 0,
				'campo24': 0,
				'campo25': 0,
				'campo26': 0
			}
		pagina_2 = 0		
		for i in self.env['account.asset.71.book'].search([]):
			first_pos = 30

			c.setFont("Helvetica", 7)
			c.drawString( first_pos+2 ,pos_inicial,( str(i.campo1 if i.campo1 else '')) )
			first_pos += size_widths[0]

			c.drawString( first_pos+2 ,pos_inicial,( str(i.campo2 if i.campo2 else '')) )
			first_pos += size_widths[1]

			c.drawString( first_pos+2 ,pos_inicial,( particionar_text(u'%s'%(str(i.campo3 if i.campo3 else '')),67)) )
			first_pos += size_widths[2]

			c.drawString( first_pos+2 ,pos_inicial,( str(i.campo4 if i.campo4 else '')) )
			first_pos += size_widths[3]

			c.drawString( first_pos+2 ,pos_inicial,( str(i.campo5 if i.campo5 else '')) )
			first_pos += size_widths[4]

			c.drawString( first_pos+2 ,pos_inicial,( str(i.campo6 if i.campo6 else '')) )
			first_pos += size_widths[5]

			c.drawRightString( first_pos+42 ,pos_inicial,( str(i.campo7 if i.campo7 else '')) )
			first_pos += size_widths[6]

			c.drawRightString( first_pos+42 ,pos_inicial,( str(i.campo8 if i.campo8 else '')) )
			first_pos += size_widths[7]

			c.drawRightString( first_pos+42 ,pos_inicial,( str(i.campo9 if i.campo9 else '')) )
			first_pos += size_widths[8]

			c.drawRightString( first_pos+42 ,pos_inicial,( str(i.campo10 if i.campo10 else '')) )
			first_pos += size_widths[9]
			
			c.drawRightString( first_pos+42 ,pos_inicial,( str(i.campo11 if i.campo11 else '')) )
			first_pos += size_widths[10]

			c.drawRightString( first_pos+42 ,pos_inicial,( str(i.campo12 if i.campo12 else '')) )
			first_pos += size_widths[11]

			c.drawRightString( first_pos+42 ,pos_inicial,( str(i.campo13 if i.campo13 else '')) )
			first_pos += size_widths[12]

			c.drawRightString( first_pos+42 ,pos_inicial,( str(i.campo14 if i.campo14 else '')) )
			first_pos += size_widths[13]

			c.drawString( first_pos+2 ,pos_inicial,( str(i.campo15 if i.campo15 else '')) )
			first_pos += size_widths[14]

			c.drawString( first_pos+2 ,pos_inicial,( str(i.campo16 if i.campo16 else '')) )
			first_pos += size_widths[15]

			c.drawString( first_pos+2 ,pos_inicial,( str(i.campo17 if i.campo17 else '')) )
			first_pos += size_widths[16]
			
			c.drawRightString( first_pos+42 ,pos_inicial,( str(i.campo18 if i.campo18 else '')) )
			first_pos += size_widths[17]

			c.drawRightString( first_pos+42 ,pos_inicial,( str(round(i.campo19, 2) if i.campo19 else '')) )
			first_pos += size_widths[18]

			c.drawRightString( first_pos+42 ,pos_inicial,( str(i.campo20 if i.campo20 else '')) )
			first_pos += size_widths[19]

			c.drawRightString( first_pos+42 ,pos_inicial,( str(round(i.campo21, 2) if i.campo21 else '')) )
			first_pos += size_widths[20]

			c.drawRightString( first_pos+42 ,pos_inicial,( str(i.campo22 if i.campo22 else '')) )
			first_pos += size_widths[21]

			c.drawRightString( first_pos+42 ,pos_inicial,( str(i.campo23 if i.campo23 else '')) )
			first_pos += size_widths[22]

			c.drawRightString( first_pos+42 ,pos_inicial,( str(round(i.campo24, 2) if i.campo24 else '')) )
			first_pos += size_widths[23]

			c.drawRightString( first_pos+42 ,pos_inicial,( str(i.campo25 if i.campo25 else '')) )
			first_pos += size_widths[24]

			c.drawRightString( first_pos+42 ,pos_inicial,( str(round(i.campo26,2) if i.campo26 else '')) )
			first_pos += size_widths[25]

			totales['campo7'] += i.campo7 or 0
			totales['campo8'] += i.campo8 or 0
			totales['campo9'] += i.campo9 or 0
			totales['campo10'] += i.campo10 or 0
			totales['campo11'] += i.campo11 or 0
			totales['campo12'] += i.campo12 or 0
			totales['campo13'] += i.campo13 or 0
			totales['campo14'] += i.campo14 or 0
			totales['campo18'] += i.campo18 or 0
			totales['campo19'] += i.campo19 or 0
			totales['campo20'] += i.campo20 or 0
			totales['campo21'] += i.campo21 or 0
			totales['campo22'] += i.campo22 or 0
			totales['campo23'] += i.campo23 or 0
			totales['campo24'] += i.campo24 or 0
			totales['campo25'] += i.campo25 or 0
			totales['campo26'] += i.campo26 or 0

			if pagina ==1:				
				pagina_2 = pagina
			if pagina_2 != pagina:
				totales_h['campo7'] = 0 
				totales_h['campo8']= 0
				totales_h['campo9'] = 0
				totales_h['campo10'] = 0
				totales_h['campo11'] = 0
				totales_h['campo12'] = 0
				totales_h['campo13'] = 0
				totales_h['campo14'] = 0
				totales_h['campo18'] = 0
				totales_h['campo19'] = 0
				totales_h['campo20'] = 0
				totales_h['campo21'] = 0
				totales_h['campo22'] = 0
				totales_h['campo23'] = 0
				totales_h['campo24'] = 0
				totales_h['campo25']= 0
				totales_h['campo26']= 0
				pagina_2 = pagina

			totales_h['campo7'] += i.campo7 or 0
			totales_h['campo8'] += i.campo8 or 0
			totales_h['campo9'] += i.campo9 or 0
			totales_h['campo10'] += i.campo10 or 0
			totales_h['campo11'] += i.campo11 or 0
			totales_h['campo12'] += i.campo12 or 0
			totales_h['campo13'] += i.campo13 or 0
			totales_h['campo14'] += i.campo14 or 0
			totales_h['campo18'] += i.campo18 or 0
			totales_h['campo19'] += i.campo19 or 0
			totales_h['campo20'] += i.campo20 or 0
			totales_h['campo21'] += i.campo21 or 0
			totales_h['campo22'] += i.campo22 or 0
			totales_h['campo23'] += i.campo23 or 0
			totales_h['campo24'] += i.campo24 or 0
			totales_h['campo25'] += i.campo25 or 0
			totales_h['campo26'] += i.campo26 or 0

			
			pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths,totales_h)
		
		first_pos_totals = 30
		c.setFont("Helvetica-Bold", 6)
		
		c.drawString(first_pos_totals +2, pos_inicial,"TOTALES")
		first_pos_totals += size_widths[1]+size_widths[2]+size_widths[3]+size_widths[4]+size_widths[5]
		
		c.drawRightString(first_pos_totals + 87, pos_inicial, '{:,.2f}'.format((totales_h['campo7'] if totales_h['campo7']!=0 else 0.0)))
		first_pos_totals += size_widths[6]
	
		c.drawRightString(first_pos_totals + 87, pos_inicial, '{:,.2f}'.format((totales_h['campo8'] if totales_h['campo8']!=0 else 0.0))) 
		first_pos_totals += size_widths[7]

		c.drawRightString(first_pos_totals + 87, pos_inicial, '{:,.2f}'.format((totales_h['campo9'] if totales_h['campo9']!=0 else 0.0))) 
		first_pos_totals += size_widths[8]

		c.drawRightString(first_pos_totals + 87, pos_inicial, '{:,.2f}'.format((totales_h['campo10'] if totales_h['campo10']!=0 else 0.0))) 
		first_pos_totals += size_widths[9]
			
		c.drawRightString(first_pos_totals + 87, pos_inicial, '{:,.2f}'.format((totales_h['campo11'] if totales_h['campo11']!=0 else 0.0))) 
		first_pos_totals += size_widths[10]

		c.drawRightString(first_pos_totals + 87, pos_inicial, '{:,.2f}'.format((totales_h['campo12'] if totales_h['campo12']!=0 else 0.0) ))
		first_pos_totals += size_widths[11]

		c.drawRightString(first_pos_totals + 87, pos_inicial, '{:,.2f}'.format((totales_h['campo13'] if totales_h['campo13']!=0 else 0.0) ))
		first_pos_totals += size_widths[12]

		c.drawRightString(first_pos_totals + 87, pos_inicial, '{:,.2f}'.format((totales_h['campo14'] if totales_h['campo14']!=0 else 0.0)) )
		first_pos_totals += size_widths[13]+size_widths[14]+size_widths[15]+size_widths[16] 
			
		c.drawRightString(first_pos_totals + 87, pos_inicial, '{:,.2f}'.format((totales_h['campo18'] if totales_h['campo18']!=0 else 0.0)) )
		first_pos_totals += size_widths[17]

		c.drawRightString( first_pos_totals + 87 ,pos_inicial,( '{:,.2f}'.format((totales_h['campo19'] if totales_h['campo19']!=0 else 0.0) )))
		first_pos_totals += size_widths[18]

		c.drawRightString(first_pos_totals + 87, pos_inicial, '{:,.2f}'.format((totales_h['campo20'] if totales_h['campo20']!=0 else 0.0))) 
		first_pos_totals += size_widths[19]

		c.drawRightString(first_pos_totals + 87 ,pos_inicial,( '{:,.2f}'.format((totales_h['campo21'] if totales_h['campo21']!=0 else 0.0)) ))
		first_pos_totals += size_widths[20]

		c.drawRightString(first_pos_totals + 87, pos_inicial, '{:,.2f}'.format((totales_h['campo22'] if totales_h['campo22']!=0 else 0.0))) 
		first_pos_totals += size_widths[21]

		c.drawRightString(first_pos_totals +  87, pos_inicial, '{:,.2f}'.format((totales_h['campo23'] if totales_h['campo23']!=0 else 0.0))) 
		first_pos_totals += size_widths[22]

		c.drawRightString(first_pos_totals +  87 ,pos_inicial,( '{:,.2f}'.format((totales_h['campo24'] if totales_h['campo24']!=0 else 0.0)) ))
		first_pos_totals += size_widths[23]

		c.drawRightString(first_pos_totals +  87, pos_inicial, '{:,.2f}'.format((totales_h['campo25'] if totales_h['campo25']!=0 else 0.0))) 
		first_pos_totals += size_widths[24]

		c.drawRightString(first_pos_totals +  87 ,pos_inicial,( '{:,.2f}'.format((totales_h['campo26'] if totales_h['campo26']!=0 else 0.0)) ))
		first_pos_totals += size_widths[25]
		#----------------------------------------------------------------------------------#
		pos_inicial -=10
		first_pos_totals = 30
		c.drawString(first_pos_totals +2, pos_inicial,"TOTALES FINALES")
		first_pos_totals += size_widths[1]+size_widths[2]+size_widths[3]+size_widths[4]+size_widths[5]
		
		c.drawRightString(first_pos_totals + 87, pos_inicial, '{:,.2f}'.format((totales['campo7'] if totales['campo7']!=0 else 0.0)))
		first_pos_totals += size_widths[6]
	
		c.drawRightString(first_pos_totals + 87, pos_inicial, '{:,.2f}'.format((totales['campo8'] if totales['campo8']!=0 else 0.0))) 
		first_pos_totals += size_widths[7]

		c.drawRightString(first_pos_totals + 87, pos_inicial, '{:,.2f}'.format((totales['campo9'] if totales['campo9']!=0 else 0.0))) 
		first_pos_totals += size_widths[8]

		c.drawRightString(first_pos_totals + 87, pos_inicial, '{:,.2f}'.format((totales['campo10'] if totales['campo10']!=0 else 0.0))) 
		first_pos_totals += size_widths[9]
			
		c.drawRightString(first_pos_totals + 87, pos_inicial, '{:,.2f}'.format((totales['campo11'] if totales['campo11']!=0 else 0.0))) 
		first_pos_totals += size_widths[10]

		c.drawRightString(first_pos_totals + 87, pos_inicial, '{:,.2f}'.format((totales['campo12'] if totales['campo12']!=0 else 0.0) ))
		first_pos_totals += size_widths[11]

		c.drawRightString(first_pos_totals + 87, pos_inicial, '{:,.2f}'.format((totales['campo13'] if totales['campo13']!=0 else 0.0) ))
		first_pos_totals += size_widths[12]

		c.drawRightString(first_pos_totals + 87, pos_inicial, '{:,.2f}'.format((totales['campo14'] if totales['campo14']!=0 else 0.0)) )
		first_pos_totals += size_widths[13]+size_widths[14]+size_widths[15]+size_widths[16] 
			
		c.drawRightString(first_pos_totals + 87, pos_inicial, '{:,.2f}'.format((totales['campo18'] if totales['campo18']!=0 else 0.0)) )
		first_pos_totals += size_widths[17]

		c.drawRightString( first_pos_totals + 87 ,pos_inicial,( '{:,.2f}'.format((totales['campo19'] if totales['campo19']!=0 else 0.0) )))
		first_pos_totals += size_widths[18]

		c.drawRightString(first_pos_totals + 87, pos_inicial, '{:,.2f}'.format((totales['campo20'] if totales['campo20']!=0 else 0.0))) 
		first_pos_totals += size_widths[19]

		c.drawRightString(first_pos_totals + 87 ,pos_inicial,( '{:,.2f}'.format((totales['campo21'] if totales['campo21']!=0 else 0.0)) ))
		first_pos_totals += size_widths[20]

		c.drawRightString(first_pos_totals + 87, pos_inicial, '{:,.2f}'.format((totales['campo22'] if totales['campo22']!=0 else 0.0))) 
		first_pos_totals += size_widths[21]

		c.drawRightString(first_pos_totals +  87, pos_inicial, '{:,.2f}'.format((totales['campo23'] if totales['campo23']!=0 else 0.0))) 
		first_pos_totals += size_widths[22]

		c.drawRightString(first_pos_totals +  87 ,pos_inicial,( '{:,.2f}'.format((totales['campo24'] if totales['campo24']!=0 else 0.0)) ))
		first_pos_totals += size_widths[23]

		c.drawRightString(first_pos_totals +  87, pos_inicial, '{:,.2f}'.format((totales['campo25'] if totales['campo25']!=0 else 0.0))) 
		first_pos_totals += size_widths[24]

		c.drawRightString(first_pos_totals +  87 ,pos_inicial,( '{:,.2f}'.format((totales['campo26'] if totales['campo26']!=0 else 0.0)) ))
		first_pos_totals += size_widths[25]

		pagina, pos_inicial = verify_linea_s(self,c,wReal,hReal,pos_inicial,5,pagina,size_widths)
		

		c.save()

		f = open(str(direccion) + name_file, 'rb')		
		return self.env['popup.it'].get_file('Libro de Activos Formato 7_1',base64.encodestring(b''.join(f.readlines())))

	def get_ple(self):
		ruc = self.company_id.partner_id.vat
		mond = self.company_id.currency_id.name

		if not ruc:
			raise UserError('No configuro el RUC de su Compañia.')

		if not mond:
			raise UserError('No configuro la moneda de su Compañia.')

		#LE + RUC + AÑO(YYYY) + MES(MM) + DIA(00) 
		name_doc = "LE"+ruc+str(self.period.date_start.year)+str('{:02d}'.format(self.period.date_start.month))+"00"
		sql_ple = self._get_sql_ple(self.fiscal_year_id.date_from,self.period.date_start,self.period.date_end,self.company_id.id,self.period.code)
		ReportBase = self.env['report.base']
		res = ReportBase.get_file_sql_export(sql_ple,'|')
		
		# IDENTIFICADOR DEL LIBRO

		name_doc += "070100"

		# CODIGO DE OPORTUNIDAD DE PRESENTACION DEL EEFF (00) +
		# INDICADOR DE OPERACIONES (1) +
		# INDICADOR DE CONTENIDO Con informacion(1), Sin informacion(0) +
		# INDICADOR DE MONEDA UTILIZADA Nuevos Soles(1), US Dolares(2) +
		# INDICADOR DE LIBRO ELECTRONICO GENERADO POR EL PLE (1)

		name_doc += "00"+"1"+("1" if len(res) > 0 else "0") + ("1" if mond == 'PEN' else "2") + "1.txt"

		return self.env['popup.it'].get_file(name_doc,res if res else base64.encodebytes(b"== Sin Registros =="))

	def _get_sql_71(self,date_fiscal_year_start,date_period_start,date_period_end,company_id,period_code=None):
		sql = """
				select row_number() OVER () AS id,
				T.campo1,
				T.campo2,
				T.campo3,
				T.campo4,
				T.campo5,
				T.campo6,
				T.campo7,
				T.campo8,
				T.campo9,
				T.campo10,
				T.campo11,
				(T.campo7+T.campo8+T.campo9+T.campo10+T.campo11) as campo12,
				T.campo13,
				(T.campo7+T.campo8+T.campo9+T.campo10+T.campo11+T.campo13) as campo14,
				T.campo15,
				T.campo16,
				T.campo17,
				T.campo18,
				T.campo19,
				T.campo20,
				T.campo21,
				T.campo22,
				T.campo23,
				(coalesce(T.campo20,0)+coalesce(T.campo21,0)+coalesce(T.campo22,0)+coalesce(T.campo23,0)) as campo24,
				T.campo25,
				(coalesce(T.campo20,0)+coalesce(T.campo21,0)+coalesce(T.campo22,0)+coalesce(T.campo23,0)+coalesce(T.campo25,0)) as campo26
				from
				(select asset.code as campo1,
				aa.code as campo2,
				asset.name as campo3,
				asset.brand as campo4,
				asset.model as campo5,
				asset.plaque as campo6,
				case
					when asset.date < '%s' then asset.value
					else 0::numeric
				end
				as campo7,
				case
					when asset.date >= '%s' then asset.value
					else 0::numeric
				end
				as campo8,
				0::numeric as campo9,
				case when asset.f_baja <= '%s' then (asset.value)*-1 else 0::numeric end as campo10,
				0::numeric as campo11,
				0::numeric as campo13,
				asset.date as campo15,
				asset.first_depreciation_manual_date as campo16,
				'Metodo Lineal' as campo17,
				asset.depreciation_authorization as campo18,
				asset.depreciation_rate as campo19,
				case 
				when t1.campo20 is not null then t1.campo20
				else 0::numeric
				end
				as campo20,
				case when '%s' = '00' then 0::numeric else coalesce(t2.campo21,0) end as campo21,
				case when asset.f_baja <= '%s' then ((case 
				when t1.campo20 is not null then t1.campo20
				else 0::numeric
				end) + (case when '%s' = '00' then 0::numeric else coalesce(t2.campo21,0) end))*-1 end as campo22,
				0::numeric as campo23,
				0::numeric as campo25,
				asset.id as asset_id
				from account_asset_asset asset
				left join account_asset_category cat on cat.id = asset.category_id
				left join account_account aa on aa.id = cat.account_asset_id
				left join (select asset_id, sum(amount) as campo20 from account_asset_depreciation_line 
				where depreciation_date < '%s'
				group by asset_id)t1 on t1.asset_id = asset.id
				left join (select asset_id, sum(amount) as campo21 from account_asset_depreciation_line 
				where (depreciation_date between '%s' and '%s')
				group by asset_id)t2 on t2.asset_id = asset.id
				where asset.company_id = %d and (asset.only_format_74 = False or asset.only_format_74 is null) and asset.state <> 'draft'
				and asset.date <= '%s' and (asset.f_baja is null or asset.f_baja >= '%s'))T
		""" % (date_fiscal_year_start.strftime('%Y/%m/%d'),
		date_fiscal_year_start.strftime('%Y/%m/%d'),
		date_period_end.strftime('%Y/%m/%d'),
		period_code[4:],date_period_end.strftime('%Y/%m/%d'),
		period_code[4:],
		date_fiscal_year_start.strftime('%Y/%m/%d'),
		date_fiscal_year_start.strftime('%Y/%m/%d'),
		date_period_end.strftime('%Y/%m/%d'),
		company_id,
		date_period_end.strftime('%Y/%m/%d'),
		date_fiscal_year_start.strftime('%Y/%m/%d'))

		return sql

	def _get_sql_ple(self,date_fiscal_year_start,date_period_start,date_period_end,company_id,period_code=None):
		sql = """
				select 
				'%s' as campo1,
				T.cuo as campo2,
				T.campo3,
				T.table_13_ple as campo4,
				T.code as campo5,
				T.table_13_ple as campo6,
				' ' AS campo7,
				T.table_18_ple as campo8,
				T.cuenta as campo9,
				T.table_19_ple as campo10,
				T.asset_name as campo11,
				T.brand as campo12,
				T.model as campo13,
				T.plaque as campo14,
				(T.campo7+T.adq_adi+T.campo9+T.campo10+T.campo11) as campo15,
				T.adq_adi as campo16,
				0::numeric as campo17,
				0::numeric as campo18,
				0::numeric as campo19,
				0::numeric as campo20,
				0::numeric as campo21,
				0::numeric as campo22,
				0::numeric as campo23,
				T.fecha_compra as campo24,
				T.fecha_uso as campo25,
				T.table_20_ple as campo26,
				T.depreciation_authorization as campo27,
				T.depreciation_rate as campo28,
				T.campo20 as campo29,
				0::numeric as campo30,
				0::numeric as campo31,
				0::numeric as campo32,
				0::numeric as campo33,
				0::numeric as campo34,
				0::numeric as campo35,
				0::numeric as campo36,
				T.campo37_ple as campo37,
				' '::text as campo38
				from
				(select asset.code,
				aa.code as cuenta,
				asset.name as asset_name,
				case
					when asset.date < '%s' then asset.value
					else 0::numeric
				end
				as campo7,
				case
					when asset.date >= '%s' then asset.value
					else 0::numeric
				end
				as adq_adi,
				0::numeric as campo9,
				0::numeric as campo10,
				0::numeric as campo11,
				0::numeric as campo13,
				TO_CHAR(asset.date::DATE, 'dd/mm/yyyy') as fecha_compra,
				TO_CHAR(asset.first_depreciation_manual_date::DATE, 'dd/mm/yyyy') as fecha_uso,
				'Metodo Lineal' as campo17,
				round(coalesce(t1.campo20,0),2) as campo20,
				asset.id as asset_id,
				asset.cuo,
				CASE
					WHEN am.is_opening_close = true AND to_char(am.date::timestamp with time zone, 'mmdd'::text) = '0101'::text THEN 'A' || am.name
					WHEN am.is_opening_close = true AND to_char(am.date::timestamp with time zone, 'mmdd'::text) = '1231'::text THEN 'C' || am.name
					ELSE 'M' || am.name
				END AS campo3,
				asset.table_13_ple,
				asset.table_18_ple,
				asset.table_19_ple,
				case when asset.brand <> '' THEN coalesce(asset.brand,'-') ELSE '-' END as brand,
				case when asset.model <> '' THEN coalesce(asset.model,'-') ELSE '-' END as model,
				case when asset.plaque <> '' THEN coalesce(asset.plaque,'-') ELSE '-' END as plaque,
				asset.table_20_ple,
				asset.depreciation_authorization,
				asset.depreciation_rate,
				asset.campo37_ple
				from account_asset_asset asset
				left join account_asset_category cat on cat.id = asset.category_id
				left join account_account aa on aa.id = cat.account_asset_id
				left join (select asset_id, sum(amount) as campo20 from account_asset_depreciation_line 
				where depreciation_date < '%s'
				group by asset_id)t1 on t1.asset_id = asset.id
				left join (select asset_id, sum(amount) as campo21 from account_asset_depreciation_line 
				where (depreciation_date between '%s' and '%s')
				group by asset_id)t2 on t2.asset_id = asset.id
				left join account_move_line aml on aml.id = asset.cuo::integer
				left join account_move am on am.id = aml.move_id
				where asset.company_id = %d and (asset.only_format_74 = False or asset.only_format_74 is null) and asset.state <> 'draft'
				and asset.date <= '%s' and (asset.f_baja is null or asset.f_baja >= '%s'))T
		""" % (period_code+'00',
		date_fiscal_year_start.strftime('%Y/%m/%d'),
		date_fiscal_year_start.strftime('%Y/%m/%d'),
		date_fiscal_year_start.strftime('%Y/%m/%d'),
		date_fiscal_year_start.strftime('%Y/%m/%d'),
		date_period_end.strftime('%Y/%m/%d'),
		company_id,
		date_period_end.strftime('%Y/%m/%d'),
		date_fiscal_year_start.strftime('%Y/%m/%d'))

		return sql