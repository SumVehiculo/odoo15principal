# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError
import base64
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
ENV_GROUPS = [
			{'name': 'ACTIVIDADES DE OPERACION' ,'code': ['E1','E2'], 'total_name': 'AUMENTO (DISM) DEL EFECTIVO Y EQUIVALENTE DE EFECTIVO PROVENIENTES DE ACTIVIDADES DE OPERACION'},
			{'name': 'ACTIVIDADES DE INVERSION' ,'code': ['E3','E4'], 'total_name': 'AUMENTO (DISM) DEL EFECTIVO Y EQUIVALENTE DE EFECTIVO PROVENIENTES DE ACTIVIDADES DE INVERSION'},
			{'name': 'ACTIVIDADES DE FINANCIAMIENTO' ,'code': ['E5','E6'], 'total_name': 'AUMENTO (DISM) DEL EFECTIVO Y EQUIVALENTE DE EFECTIVO PROVENIENTES DE ACTIVIDADES DE FINANCIAMIENTO'}
		]

class EfectiveFlowWizard(models.TransientModel):
	_name = 'efective.flow.wizard'
	_description = 'Efective Flow Wizard'

	name = fields.Char()
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	fiscal_year_id = fields.Many2one('account.fiscal.year',string='Ejercicio',required=True)
	period_ini =  fields.Many2one('account.period',string='Periodo S. I.',required=True)
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

	def _get_efective_flow_sql(self):
		sql = """
		CREATE OR REPLACE VIEW efective_flow AS 
		(
			SELECT row_number() OVER () AS id,
			*
			from get_efective_flow('{period_from}','{period_to}','{period_ini}',{company})
		)
		""".format(
				period_from = self.period_from.date_start.strftime('%Y/%m/%d'),
				period_to = self.period_to.date_end.strftime('%Y/%m/%d'),
				period_ini = self.period_ini.code,
				company = self.company_id.id
			)
		return sql

	def get_report(self):
		self._cr.execute(self._get_efective_flow_sql())
		if self.type_show == 'pdf':
			return self.get_pdf_efective_flow()
		else:
			return self.get_excel_efective_flow()

	def get_pdf_efective_flow(self):
		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		doc = SimpleDocTemplate(direccion + 'Flujo_Efectivo.pdf',pagesize=letter)
		elements = []
		style_title = ParagraphStyle(name='Center', alignment=TA_CENTER, fontSize=12, fontName="times-roman")
		style_right = ParagraphStyle(name='Center', alignment=TA_RIGHT, fontSize=9.6, fontName="times-roman")
		style_left = ParagraphStyle(name='Center', alignment=TA_LEFT, fontSize=9.6, fontName="times-roman")
		decimal_rounding = '%0.2f'
		simple_style = [('ALIGN', (0, 0), (-1, -1), 'CENTER'),
						('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]
		internal_width = [12*cm,2.5*cm]
		internal_height = [1*cm]
		spacer = Spacer(10, 20)

		elements.append(Paragraph('<strong>%s</strong>' % self.company_id.name, style_title))
		elements.append(Spacer(10, 10))
		elements.append(Paragraph('<strong>ESTADO DE FLUJOS DE EFECTIVO AL %s</strong>' % self.period_to.date_end, style_title))
		elements.append(Spacer(10, 10))
		elements.append(Paragraph('<strong>(Expresado en Nuevos Soles)</strong>', style_title))
		elements.append(spacer)
		
		for group in ENV_GROUPS:
			data, y, total = [], 0, 0
			currents_positive = self.env['efective.flow'].search([('efective_group','=',group['code'][0])])
			data.append([Paragraph('<strong>%s</strong>' % group['name'], style_left)])
			y += 1
			for current in currents_positive:
				data.append([Paragraph(current.name if current.name else '', style_left),
							 Paragraph(str(decimal_rounding % current.total) if current.total else '0.00', style_right)])
				total += current.total
				y += 1
			currents_negative = self.env['efective.flow'].search([('efective_group','=',group['code'][1])])
			data.append([Paragraph('<strong>Menos:</strong>', style_left),''])
			y += 1
			for current in currents_negative:
				data.append([Paragraph(current.name if current.name else '', style_left),
							 Paragraph(str(decimal_rounding % current.total) if current.total else '0.00', style_right)])
				total += current.total
				y += 1
			data.append([Paragraph('<strong>%s</strong>' % group['total_name'], style_left),
						 Paragraph('<strong><u>%s</u></strong>' % str(decimal_rounding % total), style_right)])
			y += 1
			t = Table(data, internal_width, y*internal_height)
			t.setStyle(TableStyle(simple_style))
			elements.append(t)
			elements.append(spacer)
		efective_equivalent = self.env['efective.flow'].search([('efective_group','in',['E1','E2','E3','E4','E5','E6'])]).mapped('total')
		t = Table([
			[Paragraph('<strong>AUMENTOS (DISM) NETO DE EFECTIVO Y EQUIVALENTE DE EFECTIVO</strong>', style_left),
			 Paragraph('<strong><u>%s</u></strong>' % str(decimal_rounding % sum(efective_equivalent)), style_right)]
		], internal_width, internal_height)
		t.setStyle(TableStyle(simple_style))
		elements.append(t)

		currents = self.env['efective.flow'].search([('efective_group','in',['E7','E8'])],order='efective_order')
		
		data, y = [], 0
		for current in currents:
			data.append([Paragraph(current.name, style_left),
						 Paragraph('<strong><u>%s</u></strong>' % str(decimal_rounding % current.total), style_right)])
			y += 1
			
		if data:
			t = Table(data, internal_width, y*internal_height)
			t.setStyle(TableStyle(simple_style))
			elements.append(t)

		final_equivalent = self.env['efective.flow'].search([('efective_group','in',['E1','E2','E3','E4','E5','E6','E7','E8'])]).mapped('total')
		t = Table([
			[Paragraph('<strong>%s</strong>' % 'SALDO AL FINALIZAR DE EFECTIVO Y EQUIVALENTE DE EFECTIVO AL FINALIZAR EL EJERCICIO', style_left),
			 Paragraph('<strong><u>%s</u></strong>' % str(decimal_rounding % sum(final_equivalent)), style_right)]
			], internal_width, internal_height)
		t.setStyle(TableStyle(simple_style))
		elements.append(t)

		doc.build(elements)

		f = open(direccion +'Flujo_Efectivo.pdf', 'rb')
		return self.env['popup.it'].get_file('Flujo Efectivo.pdf',base64.encodebytes(b''.join(f.readlines())))

	def get_excel_efective_flow(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']
		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'Flujo_Efectivo.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		####DELETING BORDERS####
		for i in ['especial2','especial1','numberdos','numbertotal']:
			formats[i].set_border(style = 0)

		import importlib
		import sys
		importlib.reload(sys)

		worksheet = workbook.add_worksheet("Flujo Efectivo")
		worksheet.set_tab_color('blue')

		worksheet.write(1,1,self.company_id.name,formats['especial2'])
		worksheet.write(2,1,'ESTADO DE FLUJOS DE EFECTIVO AL %s' % self.period_to.date_end,formats['especial2'])
		worksheet.write(3,1,'(Expresado en Nuevos Soles)',formats['especial2'])
		
		x = 5
		for group in ENV_GROUPS:
			currents_positive = self.env['efective.flow'].search([('efective_group','=',group['code'][0])])
			worksheet.write(x, 1, group['name'], formats['especial2'])
			total = 0
			x += 1
			for current in currents_positive:
				worksheet.write(x, 1, current.name if current.name else '', formats['especial1'])
				worksheet.write(x, 2, current.total if current.total else '0.00', formats['numberdos'])
				total += current.total
				x += 1
			currents_negative = self.env['efective.flow'].search([('efective_group','=',group['code'][1])])
			worksheet.write(x, 1, 'Menos:', formats['especial2'])
			x += 1
			for current in currents_negative:
				worksheet.write(x, 1, current.name if current.name else '', formats['especial1'])
				worksheet.write(x, 2, current.total if current.total else '0.00', formats['numberdos'])
				total += current.total
				x += 1
			worksheet.write(x, 1, group['total_name'], formats['especial2'])
			worksheet.write(x, 2, total, formats['numbertotal'])
			x += 2
		efective_equivalent = self.env['efective.flow'].search([('efective_group','in',['E1','E2','E3','E4','E5','E6'])]).mapped('total')
		worksheet.write(x, 1, 'AUMENTOS (DISM) NETO DE EFECTIVO Y EQUIVALENTE DE EFECTIVO', formats['especial2'])
		worksheet.write(x, 2, sum(efective_equivalent), formats['numbertotal'])
		x += 1
		currents = self.env['efective.flow'].search([('efective_group','in',['E7','E8'])],order='efective_order')
		for current in currents:
			worksheet.write(x, 1, current.name if current.name else '',formats['especial2'])
			worksheet.write(x, 2, current.total if current.total else '0.00',formats['numbertotal'])
			x += 1
		final_equivalent = self.env['efective.flow'].search([('efective_group','in',['E1','E2','E3','E4','E5','E6','E7','E8'])]).mapped('total')
		worksheet.write(x, 1, 'SALDO AL FINALIZAR DE EFECTIVO Y EQUIVALENTE DE EFECTIVO AL FINALIZAR EL EJERCICIO', formats['especial2'])
		worksheet.write(x, 2, sum(final_equivalent), formats['numbertotal'])

		widths = [10,132,16]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()
		f = open(direccion +'Flujo_Efectivo.xlsx', 'rb')
		return self.env['popup.it'].get_file('Flujo Efectivo.xlsx',base64.encodebytes(b''.join(f.readlines())))