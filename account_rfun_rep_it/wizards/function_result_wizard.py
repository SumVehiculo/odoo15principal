# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError
import base64
from lxml import etree
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, inch
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_RIGHT, TA_LEFT
ENV_GROUPS = [
			{'name': 'INGRESOS BRUTOS' ,'code': 'F1'},
			{'name': 'COSTOS OPERACIONALES' ,'code': 'F2'},
			{'name': 'UTILIDAD OPERATIVA' ,'code': 'F3'},
			{'name': 'RESULTADOS ANTES DE PARTICIPACIONES E IMPUESTOS' , 'code': 'F4'},
			{'name': 'UTILIDAD (PERDIDA) NETA ACT CONTINUAS', 'code': 'F5'},
			{'name': 'UTILIDAD (PERDIDA) NETA DEL EJERCICIO', 'code': 'F6'}
		]

class FunctionResultWizard(models.TransientModel):
	_name = 'function.result.wizard'

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
	
	def _get_function_result_sql(self):
		sql = """
		CREATE OR REPLACE VIEW function_result AS 
		(
			SELECT row_number() OVER () AS id,
			ati.name,
			ati.group_function,
			-sum(a1.balance) as total,
			ati.order_function
			from get_eeff('{date_from}','{date_to}',{company_id}) a1
			left join account_type_it ati on ati.id = a1.rubro_id
			where ati.group_function is not null
			group by ati.name,ati.group_function,ati.order_function
			order by ati.order_function
		)
		""".format(
				date_from = self.period_from.date_start.strftime('%Y/%m/%d'),
				date_to = self.period_to.date_end.strftime('%Y/%m/%d'),
				company_id = self.company_id.id
			)
		return sql

	def get_report(self):
		self._cr.execute(self._get_function_result_sql())
		if self.type_show == 'pdf':
			return self.get_pdf_function_result()
		else:
			return self.get_excel_function_result()

	def get_function_totals(self,groups,totals):
		def get_sum_group(code):
			return next(filter(lambda t: t['code'] == code, totals))['sum']
		####Totals#####
		next(filter(lambda g: g['code'] == 'F1', groups))['total'] = get_sum_group('F1')
		next(filter(lambda g: g['code'] == 'F2', groups))['total'] = get_sum_group('F2')
		operative_utility = get_sum_group('F1') + get_sum_group('F2') + get_sum_group('F3')
		next(filter(lambda g: g['code'] == 'F3', groups))['total'] = operative_utility
		tax_result = operative_utility + get_sum_group('F4')
		next(filter(lambda g: g['code'] == 'F4', groups))['total'] = tax_result
		continue_utility = tax_result + get_sum_group('F5')
		next(filter(lambda g: g['code'] == 'F5', groups))['total'] = continue_utility
		continue_excercise = continue_utility + get_sum_group('F6')
		next(filter(lambda g: g['code'] == 'F6', groups))['total'] = continue_excercise
		return groups

	def get_pdf_function_result(self):
		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		doc = SimpleDocTemplate(direccion + 'Resultado_por_Funcion.pdf',pagesize=letter)
		elements = []
		style_title = ParagraphStyle(name='Center', alignment=TA_CENTER, fontSize=12, fontName="times-roman")
		style_cell = ParagraphStyle(name='Center', alignment=TA_CENTER, fontSize=9.6, fontName="times-roman")
		style_right = ParagraphStyle(name='Center', alignment=TA_RIGHT, fontSize=9.6, fontName="times-roman")
		style_left = ParagraphStyle(name='Center', alignment=TA_LEFT, fontSize=9.6, fontName="times-roman")
		decimal_rounding = '%0.2f'
		simple_style = [('ALIGN', (0, 0), (-1, -1), 'CENTER'),
						('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]
		top_style = [('ALIGN', (0, 0), (-1, -1), 'CENTER'),
					 ('VALIGN', (0, 0), (-1, -1), 'TOP')]
		internal_width = [11*cm,2.5*cm]
		internal_height = [0.5*cm]
		spacer = Spacer(10, 20)

		elements.append(Paragraph('<strong>%s</strong>' % self.company_id.name, style_title))
		elements.append(Spacer(10, 10))
		elements.append(Paragraph('<strong>ESTADO DE RESULTADOS AL %s</strong>' % self.period_to.date_end, style_title))
		elements.append(Spacer(10, 10))
		elements.append(Paragraph('<strong>(Expresado en Nuevos Soles)</strong>', style_title))
		elements.append(spacer)

		TOTALS = self.get_totals(ENV_GROUPS)
		GROUPS = self.get_function_totals(ENV_GROUPS,TOTALS)

		data, y = [], 0
		total_F1, total_F2 = 0, 0
		for group in GROUPS:
			total_F1 += group['total'] if group['code'] == 'F1' else 0
			total_F2 += group['total'] if group['code'] == 'F2' else 0
			currents = self.env['function.result'].search([('group_function','=',group['code'])])
			for current in currents:
				data.append([Paragraph(current.name if current.name else '', style_left),
							 Paragraph(str(decimal_rounding % (current.total)) if current.total else '0.00', style_right)])
				y += 1
			if group['code'] == 'F2':
				data.append([Paragraph('<strong>%s</strong>' % group['name'], style_left),
							 Paragraph('<strong><u>%s</u></strong>' % str(decimal_rounding % group['total']), style_right)])
				y += 1
				t = Table(data, internal_width, y*internal_height)
				t.setStyle(TableStyle(simple_style))
				elements.append(t)
				elements.append(spacer)
				data, y = [], 0

				data.append([Paragraph('<strong>%s</strong>' % 'UTILIDAD BRUTA', style_left),
							 Paragraph('<strong><u>%s</u></strong>' % str(decimal_rounding % (total_F1 + total_F2)), style_right)])
				y += 1
				t = Table(data, internal_width, y*internal_height)
				t.setStyle(TableStyle(simple_style))
				elements.append(t)
				elements.append(spacer)
				data, y = [], 0
			else:
				data.append([Paragraph('<strong>%s</strong>' % group['name'], style_left),
							 Paragraph('<strong><u>%s</u></strong>' % str(decimal_rounding % group['total']), style_right)])
				y += 1
				t = Table(data, internal_width, y*internal_height)
				t.setStyle(TableStyle(simple_style))
				elements.append(t)
				elements.append(spacer)
				data, y = [], 0

		doc.build(elements)

		f = open(direccion +'Resultado_por_Funcion.pdf', 'rb')
		return self.env['popup.it'].get_file('Resultado por Funcion.pdf',base64.encodebytes(b''.join(f.readlines())))

	def get_totals(self,groups):
		TOTALS = []
		for group in groups:
			currents = self.env['function.result'].search([('group_function','=',group['code'])]).mapped('total')
			total = {'sum': sum(currents), 'code': group['code']}
			TOTALS.append(total)
		return TOTALS

	def get_excel_function_result(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']
		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'Resultado_por_Funcion.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		####DELETING BORDERS####
		for i in ['especial2','especial1','numberdos','numbertotal']:
			formats[i].set_border(style = 0)

		import importlib
		import sys
		importlib.reload(sys)

		worksheet = workbook.add_worksheet("Resultado por Funcion")
		worksheet.set_tab_color('blue')

		worksheet.write(1,1,self.company_id.name,formats['especial2'])
		worksheet.write(2,1,'ESTADO DE RESULTADOS AL %s' % self.period_to.date_end,formats['especial2'])
		worksheet.write(3,1,'(Expresado en Nuevos Soles)',formats['especial2'])

		TOTALS = self.get_totals(ENV_GROUPS)
		GROUPS = self.get_function_totals(ENV_GROUPS,TOTALS)
		
		x = 5
		total_F1, total_F2 = 0, 0
		for group in GROUPS:
			total_F1 += group['total'] if group['code'] == 'F1' else 0
			total_F2 += group['total'] if group['code'] == 'F2' else 0
			currents = self.env['function.result'].search([('group_function','=',group['code'])])
			for current in currents:
				worksheet.write(x, 1, current.name if current.name else '', formats['especial1'])
				worksheet.write(x, 2, current.total if current.total else '0.00', formats['numberdos'])
				x += 1
			if group['code'] == 'F2':
				worksheet.write(x, 1, group['name'], formats['especial2'])
				worksheet.write(x, 2, group['total'], formats['numbertotal'])
				x += 2
				worksheet.write(x, 1, 'UTILIDAD BRUTA', formats['especial2'])
				worksheet.write(x, 2, total_F1 + total_F2, formats['numbertotal'])
				x += 2
			else:
				worksheet.write(x, 1, group['name'], formats['especial2'])
				worksheet.write(x, 2, group['total'], formats['numbertotal'])
				x += 2

		widths = [10,60,16]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()
		f = open(direccion +'Resultado_por_Funcion.xlsx', 'rb')
		return self.env['popup.it'].get_file('Resultado por Funcion.xlsx',base64.encodebytes(b''.join(f.readlines())))