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

class FinancialSituationWizard(models.TransientModel):
	_name = 'financial.situation.wizard'

	name = fields.Char()
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	fiscal_year_id = fields.Many2one('account.fiscal.year',string='Ejercicio',required=True)
	period_from = fields.Many2one('account.period',string='Periodo Inicial',required=True)
	period_to = fields.Many2one('account.period',string='Periodo Final',required=True)
	type_show =  fields.Selection([('excel','Excel'),('pdf','PDF')],default='excel',string=u'Mostrar en', required=True)

	@api.onchange('company_id')
	def get_fiscal_year(self):
		if self.company_id:
			today = fields.Date.context_today(self)
			fiscal_year = self.env['account.fiscal.year'].search([('name','=',str(today.year))],limit=1)
			if fiscal_year:
				self.fiscal_year_id = fiscal_year.id
	
	def _get_financial_situation_sql(self):
		sql = """
		CREATE OR REPLACE VIEW financial_situation AS 
		(
			SELECT row_number() OVER () AS id,
			ati.name,
			ati.group_balance,
			case
				when ati.group_balance in ('B1','B2')
				then sum(a1.debe) - sum(a1.haber)
				else sum(a1.haber) - sum(a1.debe)
			end as total,
			ati.order_balance
			from get_sumas_mayor_f1('{date_from}','{date_to}',{company_id},TRUE) a1
			left join account_account a2 on a2.id=a1.account_id
			left join account_type_it ati on ati.id = a2.account_type_it_id
			where ati.group_balance is not null
			group by ati.name,ati.group_balance,ati.order_balance
			order by ati.order_balance
		)
		""".format(
				date_from = self.period_from.date_start.strftime('%Y/%m/%d'),
				date_to = self.period_to.date_end.strftime('%Y/%m/%d'),
				company_id = self.company_id.id
			)
		return sql

	def get_report(self):
		self._cr.execute(self._get_financial_situation_sql())
		if self.type_show == 'pdf':
			return self.get_pdf_financial_situation()
		else:
			return self.get_excel_financial_situation()

	def get_pdf_financial_situation(self):
		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		doc = SimpleDocTemplate(direccion + 'Situacion_Financiera.pdf',pagesize=landscape(letter))
		elements = []
		style_title = ParagraphStyle(name='Center', alignment=TA_CENTER, fontSize=12, fontName="times-roman")
		style_right = ParagraphStyle(name='Center', alignment=TA_RIGHT, fontSize=9.6, fontName="times-roman")
		style_left = ParagraphStyle(name='Center', alignment=TA_LEFT, fontSize=9.6, fontName="times-roman")
		decimal_rounding = '%0.2f'
		simple_style = [('ALIGN', (0, 0), (-1, -1), 'CENTER'),
						('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]
		top_style = [('ALIGN', (0, 0), (-1, -1), 'CENTER'),
					 ('VALIGN', (0, 0), (-1, -1), 'TOP')]
		internal_width = [7.5*cm,2.5*cm]
		internal_height = [0.5*cm]
		external_width = [10*cm,10*cm]
		spacer = Spacer(10, 20)
		currents_B1 = self.env['financial.situation'].search([('group_balance','=','B1')])
		currents_B2 = self.env['financial.situation'].search([('group_balance','=','B2')])
		currents_B3 = self.env['financial.situation'].search([('group_balance','=','B3')])
		currents_B4 = self.env['financial.situation'].search([('group_balance','=','B4')])
		currents_B5 = self.env['financial.situation'].search([('group_balance','=','B5')])

		elements.append(Paragraph('<strong>%s</strong>' % self.company_id.name, style_title))
		elements.append(Spacer(10, 10))
		elements.append(Paragraph('<strong>ESTADO DE SITUACION FINANCIERA AL %s</strong>' % self.period_to.date_end, style_title))
		elements.append(Spacer(10, 10))
		elements.append(Paragraph('<strong>(Expresado en Nuevos Soles)</strong>', style_title))
		elements.append(spacer)

		data = [
			 [Paragraph('<strong>ACTIVO</strong>',style_left),'',
			  Paragraph('<strong>PASIVO Y PATRIMONIO</strong>',style_left),'']
		]
		t = Table(data,2*internal_width)
		t.setStyle(TableStyle(simple_style))
		elements.append(t)

		elements.append(spacer)

		data = [
				[Paragraph('<strong>ACTIVO CORRIENTE</strong>',style_left),'']
			   ]
		y = 1
		total_B1 = 0
		for current in currents_B1:
			data.append([Paragraph(current.name,style_left),Paragraph(str(decimal_rounding % current.total),style_right)])
			y += 1
			total_B1 += current.total
		t1 = Table(data,internal_width,y*internal_height)
		t1.setStyle(TableStyle(simple_style))
		data = [
				[Paragraph('<strong>PASIVO CORRIENTE</strong>',style_left),'']
			   ]
		y = 1
		total_B3 = 0
		for current in currents_B3:
			data.append([Paragraph(current.name,style_left),Paragraph(str(decimal_rounding % current.total),style_right)])
			y += 1
			total_B3 += current.total
		t2 = Table(data,internal_width,y*internal_height)
		t2.setStyle(TableStyle(simple_style))
		t3 = Table([[t1,t2]],external_width)
		t3.setStyle(TableStyle(top_style))
		elements.append(t3)

		data = [
			[Paragraph('<strong>TOTAL ACTIVO CORRIENTE</strong>',style_left),
			 Paragraph('<strong><u>%s</u></strong>' % str(decimal_rounding % total_B1),style_right),
			 Paragraph('<strong>TOTAL PASIVO CORRIENTE</strong>',style_left),
			 Paragraph('<strong><u>%s</u></strong>' % str(decimal_rounding % total_B3),style_right)]
		]
		t = Table(data,2*internal_width)
		t.setStyle(TableStyle(simple_style))
		elements.append(t)

		elements.append(spacer)
		
		data = [
				[Paragraph('<strong>ACTIVO NO CORRIENTE</strong>',style_left),'']
			   ]
		y = 1
		total_B2 = 0
		for current in currents_B2:
			data.append([Paragraph(current.name,style_left),Paragraph(str(decimal_rounding % current.total),style_right)])
			y += 1
			total_B2 += current.total
		t1 = Table(data,internal_width,y*[0.8*cm])
		t1.setStyle(TableStyle(simple_style))
		data = [
				[Paragraph('<strong>PASIVO NO CORRIENTE</strong>',style_left),'']
			   ]
		y = 1
		total_B4 = 0
		for current in currents_B4:
			data.append([Paragraph(current.name,style_left),Paragraph(str(decimal_rounding % current.total),style_right)])
			y += 1
			total_B4 += current.total
		t2 = Table(data,internal_width,y*internal_height)
		t2.setStyle(TableStyle(simple_style))
		t3 = Table([[t1,t2]],external_width)
		t3.setStyle(TableStyle(top_style))
		elements.append(t3)

		data = [
			[Paragraph('<strong>TOTAL ACTIVO NO CORRIENTE</strong>',style_left),
			 Paragraph('<strong><u>%s</u></strong>' % str(decimal_rounding % total_B2),style_right),
			 Paragraph('<strong>TOTAL PASIVO NO CORRIENTE</strong>',style_left),
			 Paragraph('<strong><u>%s</u></strong>' % str(decimal_rounding % total_B4),style_right)]
		]
		t = Table(data,2*internal_width)
		t.setStyle(TableStyle(simple_style))
		elements.append(t)

		elements.append(spacer)

		data = [
				[Paragraph('<strong>PATRIMONIO</strong>',style_left),'']
			   ]
		y = 1
		total_B5 = 0
		for current in currents_B5:
			data.append([Paragraph(current.name,style_left),Paragraph(str(decimal_rounding % current.total),style_right)])
			y += 1
			total_B5 += current.total
		t2 = Table(data,internal_width,y*internal_height)
		t2.setStyle(TableStyle(simple_style))
		t3 = Table([['',t2]],external_width)
		t3.setStyle(TableStyle(top_style))
		elements.append(t3)

		data = [
			['','',
			 Paragraph('<strong>TOTAL PATRIMONIO</strong>',style_left),
			 Paragraph('<strong><u>%s</u></strong>' % str(decimal_rounding % total_B5),style_right)]
		]
		t = Table(data,2*internal_width)
		t.setStyle(TableStyle(simple_style))
		elements.append(t)

		elements.append(spacer)

		period_result = (total_B1 + total_B2) - (total_B3 + total_B4 + total_B5)
		data = [
			['','',
			 Paragraph('<strong>RESULTADO DEL PERIODO</strong>',style_left),
			 Paragraph('<strong><u>%s</u></strong>' % str(decimal_rounding % period_result),style_right)]
		]
		t = Table(data,2*internal_width)
		t.setStyle(TableStyle(simple_style))
		elements.append(t)
		data = [
			[Paragraph('<strong>TOTAL ACTIVO</strong>',style_left),
			 Paragraph('<strong><u>%s</u></strong>' % str(decimal_rounding % (total_B1 + total_B2)),style_right),
			 Paragraph('<strong>TOTAL PASIVO Y PATRIMONIO</strong>',style_left),
			 Paragraph('<strong><u>%s</u></strong>' % str(decimal_rounding % (total_B3 + total_B4 + total_B5 + period_result)),style_right)]
		]
		t = Table(data,2*internal_width)
		t.setStyle(TableStyle(simple_style))
		elements.append(t)

		doc.build(elements)

		f = open(direccion +'Situacion_Financiera.pdf', 'rb')
		return self.env['popup.it'].get_file('Situacion Financiera.pdf',base64.encodebytes(b''.join(f.readlines())))

	def get_excel_financial_situation(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']
		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'Situacion_Financiera.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)
		####DELETING BORDERS####
		for i in ['especial2','especial1','numberdos','numbertotal']:
			formats[i].set_border(style = 0)
		
		centered = workbook.add_format({'bold': True})
		centered.set_align('center')
		centered.set_align('vcenter')
		centered.set_border(style=0)
		centered.set_text_wrap()
		centered.set_font_size(11)
		centered.set_font_name('Times New Roman')

		import importlib
		import sys
		importlib.reload(sys)

		worksheet = workbook.add_worksheet("Situacion Financiera")
		worksheet.set_tab_color('blue')

		worksheet.merge_range('B1:F1', self.company_id.name, centered)
		worksheet.merge_range('B2:F2', 'ESTADO DE SITUACION FINANCIERA AL %s' % self.period_to.date_end, centered)
		worksheet.merge_range('B3:F3', '(Expresado en Nuevos Soles)', centered)
		
		####ACTIVO CORRIENTE####
		worksheet.write(5,1,'ACTIVO',formats['especial2'])
		worksheet.write(6,1,'ACTIVO CORRIENTE',formats['especial2'])
		x=7
		currents = self.env['financial.situation'].search([('group_balance','=','B1')])
		total_B1 = 0
		for current in currents:
			worksheet.write(x,1,current.name if current.name else '',formats['especial1'])
			worksheet.write(x,2,current.total if current.total else '0.00',formats['numberdos'])
			total_B1 += current.total
			x += 1
		limit_a = x
		
		####PASIVO CORRIENTE####
		worksheet.write(5,4,'PASIVO Y PATRIMONIO',formats['especial2'])		
		worksheet.write(6,4,'PASIVO CORRIENTE',formats['especial2'])
		x=7
		currents = self.env['financial.situation'].search([('group_balance','=','B3')])
		total_B3 = 0
		for current in currents:
			worksheet.write(x,4,current.name if current.name else '',formats['especial1'])
			worksheet.write(x,5,current.total if current.total else '0.00',formats['numberdos'])
			total_B3 += current.total
			x += 1
		limit_b = x
		limit = limit_a if limit_a > limit_b else limit_b

		worksheet.write(limit,1,'TOTAL ACTIVO CORRIENTE',formats['especial2'])
		worksheet.write(limit,2,total_B1,formats['numbertotal'])
		worksheet.write(limit,4,'TOTAL PASIVO CORRIENTE',formats['especial2'])
		worksheet.write(limit,5,total_B3,formats['numbertotal'])
		limit += 2

		####ACTIVO NO CORRIENTE####
		x = limit
		worksheet.write(x,1,'ACTIVO NO CORRIENTE',formats['especial2'])
		x += 1
		currents = self.env['financial.situation'].search([('group_balance','=','B2')])
		total_B2 = 0
		for current in currents:
			worksheet.write(x,1,current.name if current.name else '',formats['especial1'])
			worksheet.write(x,2,current.total if current.total else '0.00',formats['numberdos'])
			total_B2 += current.total
			x += 1
		limit_a = x

		####PASIVO NO CORRIENTE####
		x = limit
		worksheet.write(x,4,'PASIVO NO CORRIENTE',formats['especial2'])
		x += 1
		currents = self.env['financial.situation'].search([('group_balance','=','B4')])
		total_B4 = 0
		for current in currents:
			worksheet.write(x,4,current.name if current.name else '',formats['especial1'])
			worksheet.write(x,5,current.total if current.total else '0.00',formats['numberdos'])
			total_B4 += current.total
			x += 1
		limit_b = x

		limit = limit_a if limit_a > limit_b else limit_b

		worksheet.write(limit,1,'TOTAL ACTIVO NO CORRIENTE',formats['especial2'])
		worksheet.write(limit,2,total_B2,formats['numbertotal'])
		worksheet.write(limit,4,'TOTAL PASIVO NO CORRIENTE',formats['especial2'])
		worksheet.write(limit,5,total_B4,formats['numbertotal'])
		limit += 2

		####PATRIMONIO####
		x = limit
		worksheet.write(x,4,'PATRIMONIO',formats['especial2'])
		x += 1
		currents = self.env['financial.situation'].search([('group_balance','=','B5')])
		total_B5 = 0
		for current in currents:
			worksheet.write(x,4,current.name if current.name else '',formats['especial1'])
			worksheet.write(x,5,current.total if current.total else '0.00',formats['numberdos'])
			total_B5 += current.total
			x += 1
		limit = x
		worksheet.write(limit,4,'TOTAL PATRIMONIO',formats['especial2'])
		worksheet.write(limit,5,total_B5,formats['numbertotal'])
		limit += 2

		####RESULTADO DEL PERIODO####
		worksheet.write(limit,4,'RESULTADO DEL PERIODO',formats['especial2'])
		period_result = (total_B1 + total_B2) - (total_B3 + total_B4 + total_B5)
		worksheet.write(limit,5,period_result,formats['numbertotal'])
		limit += 1

		worksheet.write(limit,1,'TOTAL ACTIVO',formats['especial2'])
		worksheet.write(limit,2,(total_B1 + total_B2),formats['numbertotal'])
		worksheet.write(limit,4,'TOTAL PASIVO',formats['especial2'])
		worksheet.write(limit,5,(total_B3 + total_B4 + total_B5) + period_result,formats['numbertotal'])

		widths = [10,60,16,8,60,16,10]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()
		f = open(direccion +'Situacion_Financiera.xlsx', 'rb')
		return self.env['popup.it'].get_file('Situacion Financiera.xlsx',base64.encodebytes(b''.join(f.readlines())))