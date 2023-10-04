# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError
import base64

import codecs
import pprint

from reportlab.pdfgen import canvas
from reportlab.lib.units import inch,cm,mm
from reportlab.lib.colors import magenta, red , black , blue, gray, Color, HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import letter, A4, inch, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.utils import simpleSplit
from reportlab.lib.enums import TA_JUSTIFY,TA_CENTER,TA_LEFT,TA_RIGHT
import time

class MaturityAnalysisRep(models.TransientModel):
	_name = 'maturity.analysis.rep'
	_description = 'Maturity Analysis Rep'

	name = fields.Char()
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	date = fields.Date(string=u'Fecha',required=True,default=fields.Date.context_today)
	type_show =  fields.Selection([('pantalla','Pantalla'),('excel','Excel'),('pdf','PDF')],string=u'Mostrar en',default='pantalla')
	mayor = fields.Char(string='Mayor',size=2,help='Escriba los dos primeros digitos de que la cuenta que desea filtrar.')

	def get_receivable(self):
		return self.get_report('receivable')

	def get_payable(self):
		return self.get_report('payable')

	def get_report(self,type):
		first_date = date(self.date.year, 1, 1)
		self.env.cr.execute("""
			CREATE OR REPLACE view maturity_analysis_book as ("""+self._get_sql(first_date,self.date,self.company_id.id,type,self.mayor)+""")""")
			
		if self.type_show == 'pantalla':
			return {
				'name': 'Analisis de Vencimiento',
				'type': 'ir.actions.act_window',
				'res_model': 'maturity.analysis.book',
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

		workbook = Workbook(direccion +'Analisis_Vencimientos.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		##########ANALISIS VENCIMIENTO############
		worksheet = workbook.add_worksheet("ANALISIS VENCIMIENTO")
		worksheet.set_tab_color('blue')

		HEADERS = self._get_header_report()
		worksheet = ReportBase.get_headers(worksheet,HEADERS,0,0,formats['boldbord'])
		x=1

		for line in self.env['maturity.analysis.book'].search([]):
			worksheet.write(x,0,line.fecha_emi if line.fecha_emi else '',formats['dateformat'])
			worksheet.write(x,1,line.fecha_ven if line.fecha_ven else '',formats['dateformat'])
			worksheet.write(x,2,line.cuenta if line.cuenta else '',formats['especial1'])
			worksheet.write(x,3,line.divisa if line.divisa else '',formats['especial1'])
			worksheet.write(x,4,line.tdp if line.tdp else '',formats['especial1'])
			worksheet.write(x,5,line.doc_partner if line.doc_partner else '',formats['especial1'])
			worksheet.write(x,6,line.partner if line.partner else '',formats['especial1'])
			worksheet.write(x,7,line.td_sunat if line.td_sunat else '',formats['especial1'])
			worksheet.write(x,8,line.nro_comprobante if line.nro_comprobante else '',formats['especial1'])
			worksheet.write(x,9,line.saldo_mn if line.saldo_mn else '0.00',formats['numberdos'])
			worksheet.write(x,10,line.saldo_me if line.saldo_me else '0.00',formats['numberdos'])
			worksheet.write(x,11,line.cero_treinta if line.cero_treinta else '0.00',formats['numberdos'])
			worksheet.write(x,12,line.treinta1_sesenta if line.treinta1_sesenta else '0.00',formats['numberdos'])
			worksheet.write(x,13,line.sesenta1_noventa if line.sesenta1_noventa else '0.00',formats['numberdos'])
			worksheet.write(x,14,line.noventa1_ciento20 if line.noventa1_ciento20 else '0.00',formats['numberdos'])
			worksheet.write(x,15,line.ciento21_ciento50 if line.ciento21_ciento50 else '0.00',formats['numberdos'])
			worksheet.write(x,16,line.ciento51_ciento80 if line.ciento51_ciento80 else '0.00',formats['numberdos'])
			worksheet.write(x,17,line.ciento81_mas if line.ciento81_mas else '0.00',formats['numberdos'])
			x += 1

		widths = [10,12,8,8,6,11,40,6,21,16,16,15,15,15,15,15,15,15]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()

		f = open(direccion +'Analisis_Vencimientos.xlsx', 'rb')
		return self.env['popup.it'].get_file('Analisis_Vencimientos.xlsx',base64.encodebytes(b''.join(f.readlines())))

	def _get_header_report(self):
		headers = ['FECHA EM','FECHA VEN','CUENTA','DIVISA','TDP','RUC','PARTNER',
		'TD','NRO COMPROBANTE',u'SALDO MN',u'SALDO ME',u'0 - 30',u'31 - 60',u'61 - 90',u'91 - 120',u'121 - 150',u'151 - 180',u'181 - MÁS']

		return headers

	def getPdf(self):
		#CREANDO ARCHIVO PDF
		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		name_file = "Analisis_Vencimientos.pdf"
	
		archivo_pdf = SimpleDocTemplate(str(direccion)+name_file, pagesize=(2200,1000), rightMargin=15,leftMargin=15, topMargin=40,bottomMargin=30)

		elements = []
		style_title = ParagraphStyle(name = 'Center',alignment = TA_CENTER, fontSize = 40, fontName="Helvetica" )
		style_form = ParagraphStyle(name='Justify', alignment=TA_JUSTIFY , fontSize = 24, fontName="Helvetica" )
		style_left = ParagraphStyle(name = 'Left', alignment=TA_LEFT, fontSize=14, fontName="Helvetica")
		style_right = ParagraphStyle(name = 'Right', alignment=TA_RIGHT, fontSize=14, fontName="Helvetica")
		style_title_tab = ParagraphStyle(name = 'Center',alignment = TA_CENTER, fontSize = 15, fontName="Helvetica-Bold" )

		company = self.company_id
		texto = u'Nombre de la Compañía: ' + (company.name)
		elements.append(Paragraph(texto, style_form))
		elements.append(Spacer(1, 12))
		texto = u'Ruc de la Compañía: ' + (company.vat if company.vat else '')
		elements.append(Paragraph(texto, style_form))
		elements.append(Spacer(1, 12))
		texto = 'A Fecha: ' + str(self.date)
		elements.append(Paragraph(texto,style_form))
		elements.append(Spacer(1, 40))

		headers = self._get_header_report()
		datos = []
		datos.append([])

		for i in headers:
			datos[0].append(Paragraph(i,style_title_tab))

		for c,fila in enumerate(self.env['maturity.analysis.book'].search([])):
			datos.append([])
			datos[c+1].append(Paragraph(str(fila['fecha_emi']) if fila['fecha_emi'] else '',style_left))
			datos[c+1].append(Paragraph(str(fila['fecha_ven']) if fila['fecha_ven'] else '',style_left))
			datos[c+1].append(Paragraph((fila['cuenta']) if fila['cuenta'] else '',style_left))
			datos[c+1].append(Paragraph((fila['divisa']) if fila['divisa'] else '',style_left))
			datos[c+1].append(Paragraph((fila['tdp']) if fila['tdp'] else '',style_left))
			datos[c+1].append(Paragraph((fila['doc_partner']) if fila['doc_partner'] else '',style_left))
			datos[c+1].append(Paragraph((fila['partner']) if fila['partner'] else '',style_left))
			datos[c+1].append(Paragraph((fila['td_sunat']) if fila['td_sunat'] else '',style_left))
			datos[c+1].append(Paragraph((fila['nro_comprobante']) if fila['nro_comprobante'] else '',style_left))
			datos[c+1].append(Paragraph(str(fila['saldo_mn']) if fila['saldo_mn'] else '0.00',style_right))
			datos[c+1].append(Paragraph(str(fila['saldo_me']) if fila['saldo_me'] else '0.00',style_right))
			datos[c+1].append(Paragraph(str(fila['cero_treinta']) if fila['cero_treinta'] else '0.00',style_right))
			datos[c+1].append(Paragraph(str(fila['treinta1_sesenta']) if fila['treinta1_sesenta'] else '0.00',style_right))
			datos[c+1].append(Paragraph(str(fila['sesenta1_noventa']) if fila['sesenta1_noventa'] else '0.00',style_right))
			datos[c+1].append(Paragraph(str(fila['noventa1_ciento20']) if fila['noventa1_ciento20'] else '0.00',style_right))
			datos[c+1].append(Paragraph(str(fila['ciento21_ciento50']) if fila['ciento21_ciento50'] else '0.00',style_right))
			datos[c+1].append(Paragraph(str(fila['ciento51_ciento80']) if fila['ciento51_ciento80'] else '0.00',style_right))
			datos[c+1].append(Paragraph(str(fila['ciento81_mas']) if fila['ciento81_mas'] else '0.00',style_right))

		table_datos = Table(datos, colWidths=[3.5*cm,3.5*cm,3.5*cm,2.5*cm,1.5*cm,4*cm,15*cm,1.2*cm,6*cm,3.75*cm,3.75*cm,2.75*cm,2.75*cm,2.75*cm,2.75*cm,2.75*cm,2.75*cm,3*cm], rowHeights = len(datos)*[1*cm])

		color_cab = colors.Color(red=(220/255),green=(230/255),blue=(241/255))

		#Estilo de Tabla
		style_table = TableStyle([
				('BACKGROUND', (0, 0), (26, 0),color_cab),
				('VALIGN',(0,0),(-1,-1),'MIDDLE'),
				('GRID', (0,0), (-1,-1), 0.25, colors.black), 
				('BOX', (0,0), (-1,-1), 0.25, colors.black),
			])
		table_datos.setStyle(style_table)

		elements.append(table_datos)

		#Build
		archivo_pdf.build(elements)

		#Caracteres Especiales
		import importlib
		import sys
		importlib.reload(sys)
		import os

		f = open(str(direccion) + name_file, 'rb')		
		return self.env['popup.it'].get_file(name_file,base64.encodebytes(b''.join(f.readlines())))

	def _get_sql(self,first_date,end_date,company_id,type,mayor):
		sql_mayor = ""
		if mayor:
			sql_mayor = "WHERE left(cuenta,2) = '%s' "%(mayor)

		sql = """SELECT row_number() OVER () AS id,
				fecha_emi, fecha_ven, cuenta, divisa, tdp, 
				doc_partner, partner, td_sunat, nro_comprobante, 
				saldo_mn, saldo_me, cero_treinta, treinta1_sesenta, 
				sesenta1_noventa, noventa1_ciento20, ciento21_ciento50, 
				ciento51_ciento80, ciento81_mas
				FROM get_maturity_analysis('%s','%s',%s,'%s')
				%s
			""" % (first_date.strftime('%Y/%m/%d'),
				end_date.strftime('%Y/%m/%d'),
				str(company_id),
				str(type),
				sql_mayor)

		return sql