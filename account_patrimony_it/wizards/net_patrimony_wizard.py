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

class NetPatrimonyWizard(models.TransientModel):
	_name = 'net.patrimony.wizard'

	name = fields.Char()
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	fiscal_year_id = fields.Many2one('account.fiscal.year',string='Ejercicio',required=True)
	type_show =  fields.Selection([('pantalla','Pantalla'),('excel','Excel'),('pdf','PDF')],string=u'Mostrar en', required=True,default='pantalla')
	period_from = fields.Many2one('account.period',string='Periodo Inicial',required=True)
	period_to = fields.Many2one('account.period',string='Periodo Final',required=True)
	
	@api.onchange('company_id')
	def get_fiscal_year(self):
		if self.company_id:
			today = fields.Date.context_today(self)
			fiscal_year = self.env['account.fiscal.year'].search([('name','=',str(today.year))],limit=1)
			if fiscal_year:
				self.fiscal_year_id = fiscal_year.id

	def get_report(self):
		self.env.cr.execute("""
		CREATE OR REPLACE view account_patrimony_book as ("""+self._get_net_patrimony_sql()+""")""")
		if self.type_show == 'pantalla':
			return {
				'name': 'Patrimonio Neto',
				'type': 'ir.actions.act_window',
				'res_model': 'account.patrimony.book',
				'view_mode': 'tree',
				'view_type': 'form',
				'views': [(False, 'tree')],
			}
		if self.type_show == 'excel':
			return self.get_excel_net_patrimony()
		if self.type_show == 'pdf':
			return self.get_pdf()

	def _get_net_patrimony_sql(self):
		sql = """
			SELECT row_number() OVER () AS id, T2.* FROM 
			(SELECT am.glosa, T.capital, T.acciones,T.cap_add,T.res_no_real,
			T.exce_de_rev, T.reservas, T.res_ac, T.total FROM(SELECT 
			aml.move_id,
			SUM(CASE WHEN apt.code='001' THEN -aml.balance ELSE 0 END) AS capital,
			SUM(CASE WHEN apt.code='002' THEN -aml.balance ELSE 0 END) AS acciones,
			SUM(CASE WHEN apt.code='003' THEN -aml.balance ELSE 0 END) AS cap_add,
			SUM(CASE WHEN apt.code='004' THEN -aml.balance ELSE 0 END) AS res_no_real,
			SUM(CASE WHEN apt.code='005' THEN -aml.balance ELSE 0 END) AS exce_de_rev,
			SUM(CASE WHEN apt.code='006' THEN -aml.balance ELSE 0 END) AS reservas,
			SUM(CASE WHEN apt.code='007' THEN -aml.balance ELSE 0 END) AS res_ac,
			SUM(-aml.balance) AS total
			FROM account_move_line aml
			LEFT JOIN account_account aa ON aa.id=aml.account_id
			LEFT JOIN account_move am on am.id = aml.move_id
			LEFT JOIN  account_patrimony_type apt ON apt.id = aa.patrimony_id
			WHERE left(aa.code,1)='5' AND (am.date between '%s' AND '%s')
			AND am.company_id = %d AND am.state = 'posted' and aml.display_type is null
			GROUP BY aml.move_id)T
			LEFT JOIN account_move am ON am.id = T.move_id
			ORDER BY am.date)T2
		""" % (self.period_from.date_start.strftime('%Y/%m/%d'),
				self.period_to.date_end.strftime('%Y/%m/%d'),
				self.company_id.id)
		return sql

	def get_excel_net_patrimony(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']
		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion + 'Patrimonio_Neto.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		worksheet = workbook.add_worksheet("Patrimonio Neto")
		worksheet.set_tab_color('blue')

		worksheet.write(1,0,self.company_id.name,formats['especial2'])
		worksheet.write(2,0,'ESTADO DE CAMBIOS EN EL PATRIMONIO NETO AL %s' % self.period_to.date_end,formats['especial2'])
		worksheet.write(3,0,'(Expresado en Nuevos Soles)',formats['especial2'])		
		
		self._cr.execute(self._get_net_patrimony_sql())
		data = self._cr.dictfetchall()
		HEADERS = ['CONCEPTOS','CAPITAL','ACCIONES DE INVERSION','CAPITAL ADICIONAL','RESULTADOS NO REALIZADOS',
		'EXCEDENTE DE REVALUACION','RESERVAS','RESULTADOS ACUMULADOS','TOTALES']
		worksheet = ReportBase.get_headers(worksheet,HEADERS,5,0,formats['boldbord'])

		x = 6

		capital, acciones, cap_add, res_no_real, exce_de_rev, reservas, res_ac, total = 0, 0, 0, 0, 0, 0, 0, 0

		for line in data:
			worksheet.write(x,0,line['glosa'] if line['glosa'] else '',formats['especial1'])
			worksheet.write(x,1,line['capital'] if line['capital']  else '0.00',formats['numberdos'])
			worksheet.write(x,2,line['acciones'] if line['acciones']  else '0.00',formats['numberdos'])
			worksheet.write(x,3,line['cap_add'] if line['cap_add'] else '0.00',formats['numberdos'])
			worksheet.write(x,4,line['res_no_real'] if line['res_no_real'] else '0.00',formats['numberdos'])
			worksheet.write(x,5,line['exce_de_rev'] if line['exce_de_rev'] else '0.00',formats['numberdos'])
			worksheet.write(x,6,line['reservas'] if line['reservas'] else '0.00',formats['numberdos'])
			worksheet.write(x,7,line['res_ac'] if line['res_ac'] else '0.00',formats['numberdos'])
			worksheet.write(x,8,line['total'] if line['total'] else '0.00',formats['numbertotal'])

			capital +=line['capital'] if line['capital'] else 0
			acciones +=line['acciones'] if line['acciones'] else 0
			cap_add +=line['cap_add'] if line['cap_add'] else 0
			res_no_real +=line['res_no_real'] if line['res_no_real'] else 0
			exce_de_rev +=line['exce_de_rev'] if line['exce_de_rev'] else 0
			reservas +=line['reservas'] if line['reservas'] else 0
			res_ac +=line['res_ac'] if line['res_ac'] else 0
			total +=line['total'] if line['total'] else 0

			x += 1

		worksheet.write(x,0,'TOTALES',formats['boldbord'])
		worksheet.write(x,1,capital,formats['numbertotal'])
		worksheet.write(x,2,acciones,formats['numbertotal'])
		worksheet.write(x,3,cap_add,formats['numbertotal'])
		worksheet.write(x,4,res_no_real,formats['numbertotal'])
		worksheet.write(x,5,exce_de_rev,formats['numbertotal'])
		worksheet.write(x,6,reservas,formats['numbertotal'])
		worksheet.write(x,7,res_ac,formats['numbertotal'])
		worksheet.write(x,8,total,formats['numbertotal'])

		widths = [57,19,19,19,19,19,19,19,19]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()
		f = open(direccion +'Patrimonio_Neto.xlsx', 'rb')
		return self.env['popup.it'].get_file('Patrimonio Neto.xlsx',base64.encodebytes(b''.join(f.readlines())))

	def get_pdf(self):
		#CREANDO ARCHIVO PDF
		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		name_file = "Patrimonio_Neto.pdf"
	
		archivo_pdf = SimpleDocTemplate(str(direccion)+name_file, pagesize=(2200,1000), rightMargin=30,leftMargin=30, topMargin=30,bottomMargin=18)

		elements = []
		#Estilos 
		style_left_bold = ParagraphStyle(name = 'Right',alignment = TA_RIGHT, fontSize = 19, fontName="Helvetica-Bold" )
		style_form = ParagraphStyle(name='Justify', alignment=TA_JUSTIFY , fontSize = 24, fontName="Helvetica" )
		style_left = ParagraphStyle(name = 'Left', alignment=TA_LEFT, fontSize=19, fontName="Helvetica")
		style_right = ParagraphStyle(name = 'Right', alignment=TA_RIGHT, fontSize=19, fontName="Helvetica")
		style_title_tab = ParagraphStyle(name = 'Center',alignment = TA_CENTER, leading = 25, fontSize = 20, fontName="Helvetica-Bold" )
		

		company = self.company_id
		elements.append(Paragraph(company.name, style_form))
		elements.append(Spacer(1, 12))
		texto = 'ESTADOS DE CAMBIOS EN EL PATRIMONIO NETO AL ' + str(self.period_to.date_end)
		elements.append(Paragraph(texto, style_form))
		elements.append(Spacer(1, 12))
		texto = '(Expresado en Nuevos Soles)'
		elements.append(Paragraph(texto, style_form))
		elements.append(Spacer(1, 100))


	#Crear Tabla
		headers = ['CONCEPTOS','CAPITAL','ACCIONES DE INVERSION','CAPITAL ADICIONAL','RESULTADOS NO REALIZADOS',
		'EXCEDENTE DE REVALUACION','RESERVAS','RESULTADOS ACUMULADOS','TOTALES']

		datos = []
		datos.append([])

		for i in headers:
			datos[0].append(Paragraph(i,style_title_tab))

		x = 1
		capital, acciones, cap_add, res_no_real, exce_de_rev, reservas, res_ac, total = 0, 0, 0, 0, 0, 0, 0, 0

		self._cr.execute(self._get_net_patrimony_sql())
		data = self._cr.dictfetchall()

		for fila in data:
			datos.append([])
			datos[x].append(Paragraph((fila['glosa']) if fila['glosa'] else '',style_left))
			datos[x].append(Paragraph(str(fila['capital']) if fila['capital'] else '0.00',style_right))
			datos[x].append(Paragraph(str(fila['acciones']) if fila['acciones'] else '0.00',style_right))
			datos[x].append(Paragraph(str(fila['cap_add']) if fila['cap_add'] else '0.00',style_right))
			datos[x].append(Paragraph(str(fila['res_no_real']) if fila['res_no_real'] else '0.00',style_right))
			datos[x].append(Paragraph(str(fila['exce_de_rev']) if fila['exce_de_rev'] else '0.00',style_right))
			datos[x].append(Paragraph(str(fila['reservas']) if fila['reservas'] else '0.00',style_right))
			datos[x].append(Paragraph(str(fila['res_ac']) if fila['res_ac'] else '0.00',style_right))
			datos[x].append(Paragraph(str(fila['total']) if fila['total'] else '0.00',style_left_bold))

			capital += fila['capital'] if fila['capital'] else 0
			acciones += fila['acciones'] if fila['acciones'] else 0
			cap_add += fila['cap_add'] if fila['cap_add'] else 0
			res_no_real += fila['res_no_real'] if fila['res_no_real'] else 0
			exce_de_rev += fila['exce_de_rev'] if fila['exce_de_rev'] else 0
			reservas += fila['reservas'] if fila['reservas'] else 0
			res_ac += fila['res_ac'] if fila['res_ac'] else 0
			total += fila['total'] if fila['total'] else 0

			x += 1
		
		datos.append([])
		datos[x].append(Paragraph('TOTALES',style_title_tab))
		datos[x].append(Paragraph(str(capital),style_left_bold))
		datos[x].append(Paragraph(str(acciones),style_left_bold))
		datos[x].append(Paragraph(str(cap_add),style_left_bold))
		datos[x].append(Paragraph(str(res_no_real),style_left_bold))
		datos[x].append(Paragraph(str(exce_de_rev),style_left_bold))
		datos[x].append(Paragraph(str(reservas),style_left_bold))
		datos[x].append(Paragraph(str(res_ac),style_left_bold))
		datos[x].append(Paragraph(str(total),style_left_bold))

		table_datos = Table(datos, colWidths=[20*cm,7*cm,7*cm,7*cm,7*cm,7*cm,7*cm,7*cm,7*cm],rowHeights=[2.5*cm] + x * [1.5*cm])

		color_cab = colors.Color(red=(220/255),green=(230/255),blue=(241/255))

		#Estilo de Tabla
		style_table = TableStyle([
				('BACKGROUND', (0, 0), (8, 0),color_cab),
				('BACKGROUND', (0, x), (0, x),color_cab),
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
		return self.env['popup.it'].get_file('Patrimonio Neto.pdf',base64.encodebytes(b''.join(f.readlines())))