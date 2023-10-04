# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError
import base64
from math import modf
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4,letter, inch, landscape
from reportlab.lib.units import cm, inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak, Frame
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.pdfgen import canvas
from reportlab.lib.utils import simpleSplit
import subprocess
import sys
from datetime import *

def install(package):
	subprocess.check_call([sys.executable, "-m", "pip", "install", package])

try:
	from PyPDF2 import PdfFileReader, PdfFileWriter
except:
	install('PyPDF2')

class HrPayslip(models.Model):
	_inherit = 'hr.payslip'

	def send_vouchers_by_email(self):
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		route = MainParameter.dir_create_file + 'Boleta.pdf'
		issues = []
		for payslip in self:
			Employee = payslip.employee_id
			if MainParameter.type_boleta== '1':
				doc = SimpleDocTemplate(route, pagesize=letter,
					rightMargin=30,
					leftMargin=30,
					topMargin=30,
					bottomMargin=20,
					encrypt=Employee.identification_id)
				doc.build(payslip.generate_voucher())
			elif MainParameter.type_boleta == '2':
				objeto_canvas = canvas.Canvas(route, pagesize=A4, encrypt=Employee.identification_id)
				payslip.generate_voucher_v2(objeto_canvas)
				objeto_canvas.save()
			f = open(route, 'rb')
			try:
				self.env['mail.mail'].create({
						'subject': 'Boleta del Periodo: %s - %s' % (payslip.date_from, payslip.date_to),
						'body_html':'Estimado (a) %s,<br/>'
									'Estamos adjuntando la Boleta de Pago del %s al %s,<br/>'
									'<strong>Nota: Para abrir su boleta es necesario colocar su dni como clave</strong>' % (Employee.name, payslip.date_from, payslip.date_to),
						'email_to': Employee.work_email,
						'attachment_ids': [(0, 0, {'name': 'Boleta de Pago %s.pdf' % Employee.name,
												   'datas': base64.encodebytes(b''.join(f.readlines()))}
										)]
					}).send()
				f.close()
			except:
				issues.append(Employee.name)
		if issues:
			return self.env['popup.it'].get_message('No se pudieron enviar las Boletas de los siguientes Empleados: \n %s' % '\n'.join(issues))
		else:
			return self.env['popup.it'].get_message('Se enviaron todas las Boletas satisfactoriamente.')

	def get_vouchers(self, payslips=None):
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		if MainParameter.type_boleta== '1':
			doc = SimpleDocTemplate(MainParameter.dir_create_file + 'Boleta.pdf', pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=20)
			elements = []
			if payslips:
				for payslip in payslips:
					elements += payslip.generate_voucher()
			else:
				elements += self.generate_voucher()
			doc.build(elements)
			f = open(MainParameter.dir_create_file + 'Boleta.pdf', 'rb')
		elif MainParameter.type_boleta == '2':
			name_file = "Boleta.pdf"
			objeto_canvas  = canvas.Canvas(MainParameter.dir_create_file + name_file, pagesize=A4)
			if payslips:
				for payslip in payslips:
					payslip.generate_voucher_v2(objeto_canvas)
			else:
				self.generate_voucher_v2(objeto_canvas)
			objeto_canvas.save()
			f = open(MainParameter.dir_create_file + name_file, 'rb')
		return self.env['popup.it'].get_file('Boleta.pdf',base64.encodebytes(b''.join(f.readlines())))

	def generate_voucher(self):
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		MainParameter.check_voucher_values()
		ReportBase = self.env['report.base']
		Employee = self.employee_id
		Contract = self.contract_id
		admission_date = self.env['hr.contract'].get_first_contract(Employee, Contract).date_start

		#### WORKED DAYS ####
		DNLAB = self.worked_days_line_ids.filtered(lambda wd: wd.code in MainParameter.wd_dnlab.mapped('code'))
		DSUB = self.worked_days_line_ids.filtered(lambda wd: wd.code in MainParameter.wd_dsub.mapped('code'))
		EXT = self.worked_days_line_ids.filtered(lambda wd: wd.code in MainParameter.wd_ext.mapped('code'))
		DVAC = self.worked_days_line_ids.filtered(lambda wd: wd.code in MainParameter.wd_dvac.mapped('code'))
		DLAB = self.get_dlabs()
		# print("DLAB",DLAB)
		DLAB_DEC_INT = modf(DLAB * Contract.resource_calendar_id.hours_per_day)
		EXT_DEC_INT = modf(sum(EXT.mapped('number_of_hours')))
		DLAB = DLAB + self.holidays
		DIAS_FAL = sum(DNLAB.mapped('number_of_days'))
		DIA_VAC = sum(DVAC.mapped('number_of_days'))
		DIA_SUB = sum(DSUB.mapped('number_of_days'))
		DIAS_NLAB = DIAS_FAL + DIA_VAC + DIA_SUB

		if DIA_SUB==30:
			DIA_SUB = self.date_to.day
			DLAB = 0
			DIAS_NLAB = DIA_VAC + DIA_SUB
		elif DIA_VAC==30:
			DIA_VAC = self.date_to.day
			DLAB = 0
			DIAS_NLAB = DIA_VAC + DIA_SUB
		elif (DIA_SUB+DIA_VAC)==30:
			DIAS_NLAB = self.date_to.day
			DLAB = 0

		#### SALARY RULE CATEGORIES ####
		INCOME = self.line_ids.filtered(lambda sr: sr.category_id.id in MainParameter.income_categories.ids and sr.total > 0)
		DISCOUNTS = self.line_ids.filtered(lambda sr: sr.category_id.id in MainParameter.discounts_categories.ids and sr.total > 0)
		CONTRIBUTIONS = self.line_ids.filtered(lambda sr: sr.category_id.id in MainParameter.contributions_categories.ids and sr.total > 0)
		CONTRIBUTIONS_EMP = self.line_ids.filtered(lambda sr: sr.category_id.id in MainParameter.contributions_emp_categories.ids)
		NET_TO_PAY = self.line_ids.filtered(lambda sr: sr.salary_rule_id == MainParameter.net_to_pay_sr_id)
		SRC = {'Ingresos': INCOME, 'Descuentos': DISCOUNTS, 'Aportes Trabajador': CONTRIBUTIONS}

		if not MainParameter.dir_create_file:
			raise UserError(u'No existe un Directorio de Descarga configurado en Parametros Principales de Nomina para su Compañía')
		elements = []
		style_title = ParagraphStyle(name='Center', alignment=TA_CENTER, fontSize=12, fontName="times-roman")
		style_cell = ParagraphStyle(name='Center', alignment=TA_CENTER, fontSize=9.6, fontName="times-roman")
		style_right = ParagraphStyle(name='Center', alignment=TA_RIGHT, fontSize=9.6, fontName="times-roman")
		style_left = ParagraphStyle(name='Center', alignment=TA_LEFT, fontSize=9.6, fontName="times-roman")
		style_center = ParagraphStyle(name='Center', alignment=TA_CENTER, fontSize=9, fontName="times-roman")
		internal_width = [2.5 * cm]
		simple_style = [('ALIGN', (0, 0), (-1, -1), 'CENTER'),
						('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]
		bg_color = colors.HexColor("#c5d9f1")
		spacer = Spacer(10, 20)

		I = ReportBase.create_image(self.company_id.logo, MainParameter.dir_create_file + 'logo.jpg', 150.0, 45.0)
		data = [[I if I else '']]
		t = Table(data, [20 * cm])
		t.setStyle(TableStyle([('ALIGN', (0, 0), (0, 0), 'LEFT'),
							   ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]))
		elements.append(t)
		elements.append(spacer)

		data = [
				[Paragraph('RUC: %s' % self.company_id.vat or '', style_cell),
				 Paragraph('Empleador: %s' % self.company_id.name or '', style_cell),
				 Paragraph('Periodo: %s - %s' % (datetime.strftime((self.date_from),'%d-%m-%Y') or '', datetime.strftime((self.date_to),'%d-%m-%Y') or ''), style_cell)],
			]
		t = Table(data, [6 * cm, 8 * cm, 6 * cm], [1 * cm])
		t.setStyle(TableStyle([
				('BACKGROUND', (0, 0), (-1, -1), bg_color),
				('ALIGN', (0, 0), (-1, -1), 'CENTER'),
				('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
				('BOX', (0, 0), (-1, -1), 0.25, colors.black)
							]))
		elements.append(t)
		elements.append(spacer)

		if Contract.situation_id.name == 'BAJA':
			if self.date_from <= Contract.date_end <= self.date_to:
				situacion='BAJA'
			else:
				situacion='ACTIVO O SUBSIDIADO'
		else:
			situacion='ACTIVO O SUBSIDIADO'
		first_row = [
				[Paragraph('Documento de Identidad', style_cell), '',
				 Paragraph('Nombres y Apellidos', style_cell), '', '', '',
				 Paragraph(U'Situación', style_cell), ''],
				[Paragraph('Tipo', style_cell),
				 Paragraph(u'Número', style_cell), '', '', '', '', '', ''],
				[Paragraph(Employee.type_document_id.name or '', style_cell),
				 Paragraph(Employee.identification_id or '', style_cell),
				 Paragraph(Employee.name or '', style_cell), '', '', '',
				 Paragraph(situacion or '', style_cell), '']
			]
		first_row_format = [
				('SPAN', (0, 0), (1, 0)),
				('SPAN', (2, 0), (5, 1)),
				('SPAN', (6, 0), (7, 1)),
				('SPAN', (2, 2), (5, 2)),
				('SPAN', (6, 2), (7, 2)),
				('BACKGROUND', (0, 0), (-1, 1), bg_color)
			]
		second_row = [
				[Paragraph('Fecha de Ingreso', style_cell), '',
				 Paragraph('Tipo Trabajador', style_cell), '',
				 Paragraph('Regimen Pensionario', style_cell), '',
				 Paragraph('CUSPP', style_cell), ''],
				[Paragraph(str(datetime.strftime((admission_date),'%d-%m-%Y')) or '', style_cell), '',
				 Paragraph(Contract.worker_type_id.name or '', style_cell), '',
				 Paragraph(self.membership_id.name if self.membership_id.name else Contract.membership_id.name, style_cell), '',
				 Paragraph(Contract.cuspp or '', style_cell), '']
			]
		second_row_format =	[
				('SPAN', (0, 3), (1, 3)),
				('SPAN', (2, 3), (3, 3)),
				('SPAN', (4, 3), (5, 3)),
				('SPAN', (6, 3), (7, 3)),
				('SPAN', (0, 4), (1, 4)),
				('SPAN', (2, 4), (3, 4)),
				('SPAN', (4, 4), (5, 4)),
				('SPAN', (6, 4), (7, 4)),
				('BACKGROUND', (0, 3), (-1, 3), bg_color)
			]
		third_row = [
				[Paragraph(u'Días Laborados', style_cell),
				 Paragraph(u'Días no Laborados', style_cell),
				 Paragraph(u'Días Subsidiados', style_cell),
				 Paragraph(u'Condición', style_cell),
				 Paragraph('Jornada Ordinaria', style_cell), '',
				 Paragraph('Sobretiempo', style_cell), ''],
				['', '', '', '',
				 Paragraph('Total Horas', style_cell),
				 Paragraph('Minutos', style_cell),
				 Paragraph('Total Horas', style_cell),
				 Paragraph('Minutos', style_cell)],
				[Paragraph('%d'% DLAB or '0', style_cell),
				 Paragraph('%d'% DIAS_NLAB or '0', style_cell),
				 Paragraph('%d'% DIA_SUB or '0', style_cell),
				 Paragraph(dict(Employee._fields['condition'].selection).get(Employee.condition) or '', style_cell),
				 Paragraph(str(ReportBase.custom_round(DLAB_DEC_INT[1])) or '0', style_cell),
				 Paragraph(str(ReportBase.custom_round(DLAB_DEC_INT[0] * 60)) or '0', style_cell),
				 Paragraph(str(ReportBase.custom_round(EXT_DEC_INT[1])), style_cell),
				 Paragraph(str(ReportBase.custom_round(EXT_DEC_INT[0] * 60)) or '0', style_cell)]
			]
		third_row_format = [
				('SPAN', (0, 5), (0, 6)),
				('SPAN', (1, 5), (1, 6)),
				('SPAN', (2, 5), (2, 6)),
				('SPAN', (3, 5), (3, 6)),
				('SPAN', (4, 5), (5, 5)),
				('SPAN', (6, 5), (7, 5)),
				('BACKGROUND', (0, 5), (-1, 6), bg_color)
			]
		fourth_row = [
				[Paragraph(u'Otros empleadores por Rentas de 5ta categoría', style_cell), '', '', '',
				 Paragraph(Contract.other_employers or '', style_cell), '', '', '']
			]
		fourth_row_format = [
				('SPAN', (0, 8), (3, 8)),
				('SPAN', (4, 8), (7, 8)),
				('BACKGROUND', (0, 8), (3, 8), bg_color)
			]
		fifth_row = [
				[Paragraph(u'Motivo de Suspensión de Labores', style_cell), '', '', '', '', '', '', ''],
				[Paragraph('Tipo', style_cell),
				 Paragraph('Motivo', style_cell), '', '', '', '', '',
				 Paragraph('Nro Días', style_cell)]
			]
		fifth_row_format = [
				('SPAN', (0, 9), (-1, 9)),
				('SPAN', (1, 10), (6, 10)),
				('BACKGROUND', (0, 9), (-1, 10), bg_color)
			]
		span_limit = 11
		y = 0
		memoria=[]
		for line in Contract.work_suspension_ids.filtered(lambda payslip: payslip.payslip_run_id.id == self.payslip_run_id.id):
			# print("line",line.suspension_type_id)
			if line.suspension_type_id.code in memoria:
				continue
			total_dias = self.env['hr.work.suspension'].search([('payslip_run_id', '=', self.payslip_run_id.id),('contract_id', '=',Contract.id),
																('suspension_type_id', '=',line.suspension_type_id.id)]).mapped('days')
			# print("total_dias",sum(total_dias))
			fifth_row += [
				[Paragraph(line.suspension_type_id.code or '', style_cell),
				 Paragraph(line.reason or '', style_cell), '', '', '', '', '',
				 Paragraph(str(sum(total_dias)) or '0', style_cell)]
			]
			fifth_row_format += [('SPAN', (1, span_limit), (6, span_limit))]
			span_limit += 1
			y += 1
			memoria.append(line.suspension_type_id.code)
			# print("memoria",memoria)
		global_format = [
				('ALIGN', (0, 0), (-1, -1), 'CENTER'),
				('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
				('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
				('BOX', (0, 0), (-1, -1), 0.25, colors.black)
			]
		t = Table(first_row + second_row + third_row + fourth_row + fifth_row, 8 * internal_width, (y + 11) * [0.5 * cm])
		t.setStyle(TableStyle(first_row_format + second_row_format + third_row_format + fourth_row_format + fifth_row_format + global_format))
		elements.append(t)
		elements.append(spacer)

		data = [[
				Paragraph(u'Código', style_cell),
				Paragraph('Conceptos', style_cell),
				Paragraph('Ingresos S/.', style_cell),
				Paragraph('Descuentos S/.', style_cell),
				Paragraph('Neto S/.', style_cell)
			]]
		y = 0
		data_format = [('BACKGROUND', (0, 0), (-1, 0), bg_color)]
		for i in SRC:
			data += [[Paragraph(i, style_left), '', '', '', '']]
			y += 1
			data_format += [('SPAN', (0, y), (-1, y)),
							('BACKGROUND', (0, y), (-1, y), bg_color)]
			for line in SRC[i]:
				data += [[
						Paragraph(line.salary_rule_id.sunat_code or '', style_left),
						Paragraph(line.name or '', style_left),
						Paragraph('{:,.2f}'.format(line.total) or '0.00' if line.category_id.type == 'in' else '', style_right),
						Paragraph('{:,.2f}'.format(line.total) or '0.00' if line.category_id.type == 'out' else '', style_right), ''
					]]
				y += 1
		y += 1
		data += [[Paragraph(NET_TO_PAY.salary_rule_id.name or '', style_left), '', '', '', Paragraph('{:,.2f}'.format(NET_TO_PAY.total) or '0.00', style_right)]]
		data_format += [
			('SPAN', (0, y), (3, y)),
			('BACKGROUND', (0, y), (-1, y), bg_color),
			('ALIGN', (0, 0), (-1, -1), 'CENTER'),
			('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
			('INNERGRID', (0, 0), (-1, 0), 0.25, colors.black),
			('BOX', (0, 0), (-1, 0), 0.25, colors.black),
			('BOX', (0, 0), (-1, -1), 0.25, colors.black)
		]
		t = Table(data, [3 * cm, 8 * cm, 3 * cm, 3 * cm, 3 * cm], (y + 1) * [0.5 * cm])
		t.setStyle(TableStyle(data_format))
		elements.append(t)
		elements.append(spacer)

		data = [[Paragraph('Aportes Empleador', style_left), '', '']]
		data_format = [('SPAN', (0, 0), (-1, 0)),
					   ('BACKGROUND', (0, 0), (-1, 0), bg_color),
					   ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
					   ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
					   ('BOX', (0, 0), (-1, 0), 0.25, colors.black),
					   ('BOX', (0, 0), (-1, -1), 0.25, colors.black)]
		y = 1
		for sr in CONTRIBUTIONS_EMP:
			# print("sr.total",sr.total)
			if sr.total != 0:
				data += [[Paragraph(sr.salary_rule_id.sunat_code or '', style_left),
						  Paragraph(sr.name or '', style_left),
						  Paragraph('{:,.2f}'.format(sr.total) or '0.00', style_right)]]
				y += 1

		t = Table(data, [3 * cm, 14 * cm, 3 * cm], y * [0.5 * cm])
		t.setStyle(TableStyle(data_format))
		elements.append(t)
		elements.append(spacer)
		elements.append(spacer)
		elements.append(spacer)

		I = ReportBase.create_image(MainParameter.signature, MainParameter.dir_create_file + 'signature.jpg', 150.0, 45.0)
		data = [
			['', I if I else ''],
			[Paragraph('<strong>___________________________________<br/>%s<br/>%s N° %s<br/>Trabajador(a)</strong>' % (
				Employee.name or '', Employee.type_document_id.name or '', Employee.identification_id or ''),
					   style_center),
			 Paragraph('<strong>___________________________________<br/>%s<br/>%s N° %s<br/>Empleador</strong>' % (
				 MainParameter.reprentante_legal_id.name or '',
				 MainParameter.reprentante_legal_id.l10n_latam_identification_type_id.name or '',
				 MainParameter.reprentante_legal_id.vat or ''), style_center)],
		]
		t = Table(data, [10 * cm, 10 * cm], len(data) * [0.9 * cm])
		t.setStyle(TableStyle(simple_style))
		elements.append(t)
		elements.append(PageBreak())
		return elements

	def generate_voucher_v2(self,objeto_canvas):
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		MainParameter.check_voucher_values()
		ReportBase = self.env['report.base']
		Employee = self.employee_id
		Contract = self.contract_id
		admission_date = self.env['hr.contract'].get_first_contract(Employee, Contract).date_start

		#### WORKED DAYS ####
		DNLAB = self.worked_days_line_ids.filtered(lambda wd: wd.code in MainParameter.wd_dnlab.mapped('code'))
		DSUB = self.worked_days_line_ids.filtered(lambda wd: wd.code in MainParameter.wd_dsub.mapped('code'))
		EXT = self.worked_days_line_ids.filtered(lambda wd: wd.code in MainParameter.wd_ext.mapped('code'))
		DVAC = self.worked_days_line_ids.filtered(lambda wd: wd.code in MainParameter.wd_dvac.mapped('code'))
		DLAB = self.get_dlabs()
		# print("DLAB",DLAB)
		DLAB_DEC_INT = modf(DLAB * Contract.resource_calendar_id.hours_per_day)
		EXT_DEC_INT = modf(sum(EXT.mapped('number_of_hours')))
		DLAB = DLAB + self.holidays
		DIAS_FAL = sum(DNLAB.mapped('number_of_days'))
		DIA_VAC = sum(DVAC.mapped('number_of_days'))
		DIA_SUB = sum(DSUB.mapped('number_of_days'))
		DIAS_NLAB = DIAS_FAL + DIA_VAC + DIA_SUB

		if DIA_SUB == 30:
			DIA_SUB = self.date_to.day
			DLAB = 0
			DIAS_NLAB = DIA_VAC + DIA_SUB
		elif DIA_VAC == 30:
			DIA_VAC = self.date_to.day
			DLAB = 0
			DIAS_NLAB = DIA_VAC + DIA_SUB
		elif (DIA_SUB + DIA_VAC) == 30:
			DIAS_NLAB = self.date_to.day
			DLAB = 0


		#### SALARY RULE CATEGORIES ####
		INCOME = self.line_ids.filtered(lambda sr: sr.category_id.id in MainParameter.income_categories.ids and sr.total > 0)
		DISCOUNTS = self.line_ids.filtered(lambda sr: sr.category_id.id in MainParameter.discounts_categories.ids and sr.total > 0)
		CONTRIBUTIONS = self.line_ids.filtered(lambda sr: sr.category_id.id in MainParameter.contributions_categories.ids and sr.total > 0)
		CONTRIBUTIONS_EMP = self.line_ids.filtered(lambda sr: sr.category_id.id in MainParameter.contributions_emp_categories.ids)
		NET_TO_PAY = self.line_ids.filtered(lambda sr: sr.salary_rule_id == MainParameter.net_to_pay_sr_id)

		if not MainParameter.dir_create_file:
			raise UserError(u'No existe un Directorio de Descarga configurado en Parametros Principales de Nomina para su Compañía')

		style_title = ParagraphStyle(name='Center', alignment=TA_CENTER, fontSize=8, fontName="times-roman")
		style_cell = ParagraphStyle(name='Center', alignment=TA_CENTER, fontSize=9.6, fontName="times-roman")
		style_right = ParagraphStyle(name='Center', alignment=TA_RIGHT, fontSize=9.6, fontName="times-roman")
		style_left = ParagraphStyle(name='Center', alignment=TA_LEFT, fontSize=9.6, fontName="times-roman")
		internal_width = [2.5 * cm]
		bg_color = colors.HexColor("#c5d9f1")
		spacer = Spacer(10, 20)

		width ,height  = A4  # 595 , 842
		wReal = width- 15
		hReal = height - 40
		pagina = 1
		size_widths = [110,50]

		if Contract.situation_id.name == 'BAJA':
			if self.date_from <= Contract.date_end <= self.date_to:
				date_end = Contract.date_end
			else:
				date_end = False
		else:
			date_end = False

		# PRIMERA COPIA BOLETA DE PAGO
		I = ReportBase.create_image(self.company_id.logo, MainParameter.dir_create_file + 'logo.jpg', 110.0, 45.0)
		data = [
			[Paragraph('<strong>%s</strong>' % self.company_id.name or '', style_left),I if I else ''],
			[Paragraph('%s' % self.company_id.street_name or '', style_left),''],
			[Paragraph('RUC N° %s' % self.company_id.vat or '', style_left),''],
		]
		t = Table(data, [16 * cm, 4 * cm],len(data) * [0.4 * cm])
		t.setStyle(TableStyle([
			('SPAN', (1, 0), (1, -1)),
			# ('SPAN', (2, 2), (-1, -1)),
			('ALIGN', (0, 0), (0, 0), 'CENTER'),
			('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
			# ('BACKGROUND', (2, 1), (2, 1), colors.HexColor("#B0B0B0")),
			# ('BOX', (2, 0), (-1, -1), 0.25, colors.black)
		]))
		t.wrapOn(objeto_canvas,20,500)
		t.drawOn(objeto_canvas,20,hReal-15)

		objeto_canvas.setFont("Helvetica-Bold", 11)
		objeto_canvas.setFillColor(colors.black)
		objeto_canvas.drawCentredString((wReal/2)+20,hReal-30, "BOLETA DE REMUNERACIONES")
		objeto_canvas.setFont("Helvetica-Bold", 10)
		objeto_canvas.drawCentredString((wReal/2)+20,hReal-42, "PLANILLA %s" % self.payslip_run_id.name.name or '')

		objeto_canvas.setFont("Helvetica", 10)
		style = getSampleStyleSheet()["Normal"]
		style.leading = 8
		style.alignment= 1

		data = [
			[Paragraph('<strong>__________________________________________________________________________________________________________________</strong>', style_left)]
		]
		t = Table(data, [20 * cm],len(data) * [0.12 * cm])
		t.setStyle(TableStyle([
			('ALIGN', (0, 0), (0, 0), 'CENTER'),
			('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
		]))
		t.wrapOn(objeto_canvas, 20, 500)
		t.drawOn(objeto_canvas, 20, hReal - 45)

		dias_vaca = 0
		fecha_ing_vac = fecha_fin_vac = ''
		if len(self.accrual_vacation_ids) > 0:
			estado_vaca = 'SI'
			for vacaciones in self.accrual_vacation_ids:
				dias_vaca += vacaciones.days
				fecha_ing_vac = vacaciones.request_date_from
				fecha_fin_vac = vacaciones.request_date_to
		else:
			estado_vaca = 'NO'

		data = [
				[Paragraph('<strong>Trabajador</strong>', style_left),Paragraph(': %s' % Employee.name.title() or '', style_left),
				 Paragraph('<strong>Fecha de Ingreso</strong>', style_left),Paragraph(': %s' % str(datetime.strftime((admission_date),'%d-%m-%Y')) or '', style_left),
				 Paragraph('<strong>Dias Lab</strong>', style_left),Paragraph(': %d' % DLAB or '', style_left)],
				[Paragraph('<strong>Tipo Trab</strong>', style_left),Paragraph(': %s' % Contract.worker_type_id.name.capitalize() if Contract.worker_type_id.name else '', style_left),
				 Paragraph('<strong>Fecha de Cese</strong>', style_left),Paragraph(': %s' % datetime.strftime(date_end,'%d-%m-%Y') if date_end else '', style_left),
				 Paragraph('<strong>Dias Subs</strong>', style_left),Paragraph(': %d'% DIA_SUB or '0', style_left)],
				[Paragraph('<strong>Area</strong>', style_left),Paragraph(': %s' % Contract.department_id.name.capitalize() if Contract.department_id.name else '', style_left),
				 Paragraph('<strong>Periodo Vacac</strong>', style_left),Paragraph(': %s' % estado_vaca or '', style_left),
				 Paragraph('<strong>Dias No Lab</strong>', style_left),Paragraph(': %d'% DIAS_NLAB or '0', style_left)],
				[Paragraph('<strong>Cargo</strong>', style_left),Paragraph(': %s' % Contract.job_id.name.capitalize() if Contract.job_id.name else '', style_left),
				 Paragraph('<strong>&nbsp; &nbsp;&nbsp; &nbsp; Inicio Vac</strong>', style_left),Paragraph(': %s' % datetime.strftime((fecha_ing_vac),'%d-%m-%Y') if fecha_ing_vac != '' else '', style_left),
				 Paragraph('<strong>Dias Vac</strong>', style_left),Paragraph(': %d' % dias_vaca or '0', style_left)],
				[Paragraph('<strong>Centro de Costos</strong>', style_left),Paragraph(': %s' % self.distribution_id.description.capitalize() if self.distribution_id.description else self.distribution_id.name, style_left),
				 Paragraph('<strong>&nbsp; &nbsp;&nbsp; &nbsp; Fin Vac</strong>', style_left),Paragraph(': %s' % datetime.strftime((fecha_fin_vac),'%d-%m-%Y') if fecha_fin_vac != '' else '', style_left),
				 Paragraph('<strong>N° Horas Ord</strong>', style_left),Paragraph(': %s' %str(ReportBase.custom_round(DLAB_DEC_INT[1])) or '0', style_left)],
				[Paragraph('<strong>Tipo de Docum</strong>', style_left),Paragraph(': %s <strong>Nro.</strong> %s' % (Employee.type_document_id.name or '',Employee.identification_id or ''), style_left),
				 Paragraph('<strong>Reg Pensionario</strong>', style_left),Paragraph(': %s' % self.membership_id.name.title() if self.membership_id.name else Contract.membership_id.name, style_left),
				 Paragraph('<strong>N° Horas Ext</strong>', style_left),Paragraph(': %s' %str(ReportBase.custom_round(EXT_DEC_INT[1])) or '', style_left)],
				[Paragraph('<strong>Regimen Laboral</strong>', style_left),Paragraph(': %s' % dict(self._fields['labor_regime'].selection).get(self.labor_regime) or '', style_left),
				 Paragraph('<strong>C.U.S.P.P.</strong>', style_left),Paragraph(': %s' % Contract.cuspp if Contract.cuspp else '', style_left),
				 Paragraph('<strong>Rem Basica</strong>', style_left),Paragraph(': {:,.2f}'.format(self.wage) or '0.00', style_left)],

		]
		t = Table(data, [3 * cm, 6 * cm , 3 * cm, 3 * cm, 3 * cm, 2 * cm], len(data) * [0.42 * cm])
		t.setStyle(TableStyle([
			('ALIGN', (0, 0), (0, 0), 'CENTER'),
			('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
		]))
		t.wrapOn(objeto_canvas,20,500)
		t.drawOn(objeto_canvas,20,hReal-135)

		data = [[
				Paragraph('<strong>INGRESOS</strong>', style_cell),
				Paragraph('<strong>DESCUENTOS</strong>', style_cell),
				Paragraph('<strong>APORTES EMPLEADOR</strong>', style_cell)
			]]
		t = Table(data, [7 * cm,7 * cm, 6 * cm], len(data) * [0.6 * cm])
		t.setStyle(TableStyle([
			('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#B0B0B0")),
			('ALIGN', (0, 0), (0, 0), 'CENTER'),
			('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
			('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
			('BOX', (0, 0), (-1, -1), 0.25, colors.black)
		]))
		t.wrapOn(objeto_canvas,18,500)
		t.drawOn(objeto_canvas,18,hReal-160)

		def particionar_text(c,tam):
			tet = ""
			for i in range(len(c)):
				tet += c[i]
				lines = simpleSplit(tet,'Helvetica',8,tam)
				if len(lines)>1:
					return tet[:-1]
			return tet

		def verify_linea(self,c,wReal,hReal,posactual,valor,pagina,size_widths):
			if posactual <50:
				c.showPage()
				return pagina+1,hReal-142
			else:
				return pagina,posactual-valor

		h_ing = h_des = h_apor = hReal-170
		total_ing = total_des = total_apor = 0
		for ingreso in INCOME:
			objeto_canvas.setFont("Times-Roman", 9.6)
			first_pos = 20
			objeto_canvas.drawString(first_pos,h_ing,particionar_text(ingreso.name if ingreso.name else '',110) )
			first_pos += size_widths[0]
			objeto_canvas.drawRightString(first_pos+80 ,h_ing,'{:,.2f}'.format(ingreso.total) if ingreso.total else '0.00')
			first_pos += size_widths[1]

			total_ing += ingreso.total
			pagina, h_ing = verify_linea(self,objeto_canvas,wReal,hReal,h_ing,12,pagina,size_widths)

		for descuento in CONTRIBUTIONS:
			objeto_canvas.setFont("Times-Roman", 9.6)
			first_pos = 220
			objeto_canvas.drawString(first_pos,h_des,particionar_text(descuento.name if descuento.name else '',110) )
			first_pos += size_widths[0]
			objeto_canvas.drawRightString(first_pos+80 ,h_des,'{:,.2f}'.format(descuento.total) if descuento.total else '0.00')
			first_pos += size_widths[1]

			total_des += descuento.total
			pagina, h_des = verify_linea(self,objeto_canvas,wReal,hReal,h_des,12,pagina,size_widths)

		for descuento in DISCOUNTS:
			objeto_canvas.setFont("Times-Roman", 9.6)
			first_pos = 220
			objeto_canvas.drawString(first_pos,h_des,particionar_text(descuento.name if descuento.name else '',110) )
			first_pos += size_widths[0]
			objeto_canvas.drawRightString(first_pos+80 ,h_des,'{:,.2f}'.format(descuento.total) if descuento.total else '0.00')
			first_pos += size_widths[1]

			total_des += descuento.total
			pagina, h_des = verify_linea(self,objeto_canvas,wReal,hReal,h_des,12,pagina,size_widths)

		for aporte in CONTRIBUTIONS_EMP:
			objeto_canvas.setFont("Times-Roman", 9.6)
			first_pos = 420
			objeto_canvas.drawString(first_pos,h_apor,particionar_text(aporte.name if aporte.name else '',110) )
			first_pos += size_widths[0]
			objeto_canvas.drawRightString(first_pos+50 ,h_apor,'{:,.2f}'.format(aporte.total) if aporte.total else '0.00')
			first_pos += size_widths[1]

			total_apor += aporte.total
			pagina, h_apor = verify_linea(self,objeto_canvas,wReal,hReal,h_apor,12,pagina,size_widths)

		data = [[
			Paragraph('TOTAL INGRESOS S/', style_title),Paragraph('<strong>{:,.2f}</strong>'.format(total_ing) or '0.00', style_right),
			Paragraph('TOTAL DESCUENTOS S/', style_title),Paragraph('<strong>{:,.2f}</strong>'.format(total_des) or '0.00', style_right),
			Paragraph('TOTAL APORTES S/', style_title),Paragraph('<strong>{:,.2f}</strong>'.format(total_apor) or '0.00', style_right)
		]]
		t = Table(data, [5 * cm,2 * cm, 5 * cm,2 * cm, 4 * cm,2 * cm,], len(data) * [0.6 * cm])
		t.setStyle(TableStyle([
			('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#B0B0B0")),
			('ALIGN', (0, 0), (0, 0), 'CENTER'),
			('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
			# ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
			('BOX', (0, 0), (1, -1), 0.25, colors.black),
			('BOX', (2, 0), (3, -1), 0.25, colors.black),
			('BOX', (4, 0), (5, -1), 0.25, colors.black),
		]))
		t.wrapOn(objeto_canvas, 18, 500)
		t.drawOn(objeto_canvas, 18, hReal - 290)

		data = [['',
			Paragraph('<strong>NETO A PAGAR S/</strong>', style_cell),Paragraph('<strong>{:,.2f}</strong>'.format(NET_TO_PAY.total) or '0.00', style_cell),''
		]]
		t = Table(data, [7 * cm,4 * cm, 3 * cm,6 * cm], len(data) * [0.6 * cm])
		t.setStyle(TableStyle([
			('BACKGROUND', (1, 0), (1, -1), colors.HexColor("#B0B0B0")),
			('ALIGN', (0, 0), (0, 0), 'CENTER'),
			('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
			('INNERGRID', (1, 0), (2, -1), 0.25, colors.black),
			('BOX', (1, 0), (2, -1), 0.25, colors.black),
		]))
		t.wrapOn(objeto_canvas, 18, 500)
		t.drawOn(objeto_canvas, 18, hReal - 315)

		I = ReportBase.create_image(MainParameter.signature, MainParameter.dir_create_file + 'signature.jpg', 160.0, 35.0)
		data = [
				[I if I else '',''],
				[Paragraph('<strong>__________________________</strong>', style_title),
				 Paragraph('<strong>__________________________</strong>', style_title)],
				[Paragraph('<strong>EMPLEADOR</strong>', style_title),
				 Paragraph('<strong>RECIBI CONFORME <br/> TRABAJADOR</strong>', style_title)]
			]
		t = Table(data, [10 * cm, 10 * cm], 3 * [0.5 * cm])
		t.setStyle(TableStyle([
			('ALIGN', (0, 0), (0, 0), 'CENTER'),
			('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
		]))
		t.wrapOn(objeto_canvas, 18, 500)
		t.drawOn(objeto_canvas, 18, hReal - 380)




		# SEGUNDA COPIA BOLETA DE PAGO
		I = ReportBase.create_image(self.company_id.logo, MainParameter.dir_create_file + 'logo.jpg', 110.0, 45.0)
		data = [
			[Paragraph('<strong>%s</strong>' % self.company_id.name or '', style_left),I if I else ''],
			[Paragraph('%s' % self.company_id.street_name or '', style_left),''],
			[Paragraph('RUC N° %s' % self.company_id.vat or '', style_left),''],
		]
		t = Table(data, [16 * cm, 4 * cm],len(data) * [0.4 * cm])
		t.setStyle(TableStyle([
			('SPAN', (1, 0), (1, -1)),
			# ('SPAN', (2, 2), (-1, -1)),
			('ALIGN', (0, 0), (0, 0), 'CENTER'),
			('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
			# ('BACKGROUND', (2, 1), (2, 1), colors.HexColor("#B0B0B0")),
			# ('BOX', (2, 0), (-1, -1), 0.25, colors.black)
		]))
		t.wrapOn(objeto_canvas,20,500)
		t.drawOn(objeto_canvas,20,hReal-430)

		objeto_canvas.setFont("Helvetica-Bold", 11)
		objeto_canvas.setFillColor(colors.black)
		objeto_canvas.drawCentredString((wReal/2)+20,hReal-445, "BOLETA DE REMUNERACIONES")
		objeto_canvas.setFont("Helvetica-Bold", 10)
		objeto_canvas.drawCentredString((wReal/2)+20,hReal-457, "PLANILLA %s" % self.payslip_run_id.name.name or '')

		objeto_canvas.setFont("Helvetica", 10)
		style = getSampleStyleSheet()["Normal"]
		style.leading = 8
		style.alignment= 1

		data = [
			[Paragraph('<strong>__________________________________________________________________________________________________________________</strong>', style_left)]
		]
		t = Table(data, [20 * cm],len(data) * [0.12 * cm])
		t.setStyle(TableStyle([
			('ALIGN', (0, 0), (0, 0), 'CENTER'),
			('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
		]))
		t.wrapOn(objeto_canvas, 20, 500)
		t.drawOn(objeto_canvas, 20, hReal - 460)

		data = [
				[Paragraph('<strong>Trabajador</strong>', style_left),Paragraph(': %s' % Employee.name.title() or '', style_left),
				 Paragraph('<strong>Fecha de Ingreso</strong>', style_left),Paragraph(': %s' % str(datetime.strftime((admission_date),'%d-%m-%Y')) or '', style_left),
				 Paragraph('<strong>Dias Lab</strong>', style_left),Paragraph(': %d' % DLAB or '', style_left)],
				[Paragraph('<strong>Tipo Trab</strong>', style_left),Paragraph(': %s' % Contract.worker_type_id.name.capitalize() if Contract.worker_type_id.name else '', style_left),
				 Paragraph('<strong>Fecha de Cese</strong>', style_left),Paragraph(': %s' % datetime.strftime(date_end,'%d-%m-%Y') if date_end else '', style_left),
				 Paragraph('<strong>Dias Subs</strong>', style_left),Paragraph(': %d'% DIA_SUB or '0', style_left)],
				[Paragraph('<strong>Area</strong>', style_left),Paragraph(': %s' % Contract.department_id.name.capitalize() if Contract.department_id.name else '', style_left),
				 Paragraph('<strong>Periodo Vacac</strong>', style_left),Paragraph(': %s' % estado_vaca or '', style_left),
				 Paragraph('<strong>Dias No Lab</strong>', style_left),Paragraph(': %d'% DIAS_NLAB or '0', style_left)],
				[Paragraph('<strong>Cargo</strong>', style_left),Paragraph(': %s' % Contract.job_id.name.capitalize() if Contract.job_id.name else '', style_left),
				 Paragraph('<strong>&nbsp; &nbsp;&nbsp; &nbsp; Inicio Vac</strong>', style_left),Paragraph(': %s' % datetime.strftime((fecha_ing_vac),'%d-%m-%Y') if fecha_ing_vac != '' else '', style_left),
				 Paragraph('<strong>Dias Vac</strong>', style_left),Paragraph(': %d' %dias_vaca or '0', style_left)],
				[Paragraph('<strong>Centro de Costos</strong>', style_left),Paragraph(': %s' % self.distribution_id.description.capitalize() if self.distribution_id.description else self.distribution_id.name, style_left),
				 Paragraph('<strong>&nbsp; &nbsp;&nbsp; &nbsp; Fin Vac</strong>', style_left),Paragraph(': %s' % datetime.strftime((fecha_fin_vac),'%d-%m-%Y') if fecha_fin_vac != '' else '', style_left),
				 Paragraph('<strong>N° Horas Ord</strong>', style_left),Paragraph(': %s' %str(ReportBase.custom_round(DLAB_DEC_INT[1])) or '0', style_left)],
				[Paragraph('<strong>Tipo de Docum</strong>', style_left),Paragraph(': %s <strong>Nro.</strong> %s' % (Employee.type_document_id.name or '',Employee.identification_id or ''), style_left),
				 Paragraph('<strong>Reg Pensionario</strong>', style_left),Paragraph(': %s' % self.membership_id.name.title() if self.membership_id.name else Contract.membership_id.name, style_left),
				 Paragraph('<strong>N° Horas Ext</strong>', style_left),Paragraph(': %s' %str(ReportBase.custom_round(EXT_DEC_INT[1])) or '', style_left)],
				[Paragraph('<strong>Regimen Laboral</strong>', style_left),Paragraph(': %s' % dict(self._fields['labor_regime'].selection).get(self.labor_regime) or '', style_left),
				 Paragraph('<strong>C.U.S.P.P.</strong>', style_left),Paragraph(': %s' % Contract.cuspp if Contract.cuspp else '', style_left),
				 Paragraph('<strong>Rem Basica</strong>', style_left),Paragraph(': {:,.2f}'.format(self.wage) or '0.00', style_left)],

		]
		t = Table(data, [3 * cm, 6 * cm , 3 * cm, 3 * cm, 3 * cm, 2 * cm], len(data) * [0.42 * cm])
		t.setStyle(TableStyle([
			('ALIGN', (0, 0), (0, 0), 'CENTER'),
			('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
		]))
		t.wrapOn(objeto_canvas,20,500)
		t.drawOn(objeto_canvas,20,hReal-550)

		data = [[
				Paragraph('<strong>INGRESOS</strong>', style_cell),
				Paragraph('<strong>DESCUENTOS</strong>', style_cell),
				Paragraph('<strong>APORTES EMPLEADOR</strong>', style_cell)
			]]
		t = Table(data, [7 * cm,7 * cm, 6 * cm], len(data) * [0.6 * cm])
		t.setStyle(TableStyle([
			('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#B0B0B0")),
			('ALIGN', (0, 0), (0, 0), 'CENTER'),
			('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
			('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
			('BOX', (0, 0), (-1, -1), 0.25, colors.black)
		]))
		t.wrapOn(objeto_canvas,18,500)
		t.drawOn(objeto_canvas,18,hReal-575)

		h_ing = h_des = h_apor = hReal-585
		total_ing = total_des = total_apor = 0
		for ingreso in INCOME:
			objeto_canvas.setFont("Times-Roman", 9.6)
			first_pos = 20
			objeto_canvas.drawString(first_pos,h_ing,particionar_text(ingreso.name if ingreso.name else '',110) )
			first_pos += size_widths[0]
			objeto_canvas.drawRightString(first_pos+80 ,h_ing,'{:,.2f}'.format(ingreso.total) if ingreso.total else '0.00')
			first_pos += size_widths[1]

			total_ing += ingreso.total
			pagina, h_ing = verify_linea(self,objeto_canvas,wReal,hReal,h_ing,12,pagina,size_widths)

		for descuento in CONTRIBUTIONS:
			objeto_canvas.setFont("Times-Roman", 9.6)
			first_pos = 220
			objeto_canvas.drawString(first_pos,h_des,particionar_text(descuento.name if descuento.name else '',110) )
			first_pos += size_widths[0]
			objeto_canvas.drawRightString(first_pos+80 ,h_des,'{:,.2f}'.format(descuento.total) if descuento.total else '0.00')
			first_pos += size_widths[1]

			total_des += descuento.total
			pagina, h_des = verify_linea(self,objeto_canvas,wReal,hReal,h_des,12,pagina,size_widths)

		for descuento in DISCOUNTS:
			objeto_canvas.setFont("Times-Roman", 9.6)
			first_pos = 220
			objeto_canvas.drawString(first_pos,h_des,particionar_text(descuento.name if descuento.name else '',110) )
			first_pos += size_widths[0]
			objeto_canvas.drawRightString(first_pos+80 ,h_des,'{:,.2f}'.format(descuento.total) if descuento.total else '0.00')
			first_pos += size_widths[1]

			total_des += descuento.total
			pagina, h_des = verify_linea(self,objeto_canvas,wReal,hReal,h_des,12,pagina,size_widths)

		for aporte in CONTRIBUTIONS_EMP:
			objeto_canvas.setFont("Times-Roman", 9.6)
			first_pos = 420
			objeto_canvas.drawString(first_pos,h_apor,particionar_text(aporte.name if aporte.name else '',110) )
			first_pos += size_widths[0]
			objeto_canvas.drawRightString(first_pos+50 ,h_apor,'{:,.2f}'.format(aporte.total) if aporte.total else '0.00')
			first_pos += size_widths[1]

			total_apor += aporte.total
			pagina, h_apor = verify_linea(self,objeto_canvas,wReal,hReal,h_apor,12,pagina,size_widths)

		data = [[
			Paragraph('TOTAL INGRESOS S/', style_title),Paragraph('<strong>{:,.2f}</strong>'.format(total_ing) or '0.00', style_right),
			Paragraph('TOTAL DESCUENTOS S/', style_title),Paragraph('<strong>{:,.2f}</strong>'.format(total_des) or '0.00', style_right),
			Paragraph('TOTAL APORTES S/', style_title),Paragraph('<strong>{:,.2f}</strong>'.format(total_apor) or '0.00', style_right)
		]]
		t = Table(data, [5 * cm,2 * cm, 5 * cm,2 * cm, 4 * cm,2 * cm,], len(data) * [0.6 * cm])
		t.setStyle(TableStyle([
			('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#B0B0B0")),
			('ALIGN', (0, 0), (0, 0), 'CENTER'),
			('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
			# ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
			('BOX', (0, 0), (1, -1), 0.25, colors.black),
			('BOX', (2, 0), (3, -1), 0.25, colors.black),
			('BOX', (4, 0), (5, -1), 0.25, colors.black),
		]))
		t.wrapOn(objeto_canvas, 18, 500)
		t.drawOn(objeto_canvas, 18, hReal - 705)

		data = [['',
			Paragraph('<strong>NETO A PAGAR S/</strong>', style_cell),Paragraph('<strong>{:,.2f}</strong>'.format(NET_TO_PAY.total) or '0.00', style_cell),''
		]]
		t = Table(data, [7 * cm,4 * cm, 3 * cm,6 * cm], len(data) * [0.6 * cm])
		t.setStyle(TableStyle([
			('BACKGROUND', (1, 0), (1, -1), colors.HexColor("#B0B0B0")),
			('ALIGN', (0, 0), (0, 0), 'CENTER'),
			('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
			('INNERGRID', (1, 0), (2, -1), 0.25, colors.black),
			('BOX', (1, 0), (2, -1), 0.25, colors.black),
		]))
		t.wrapOn(objeto_canvas, 18, 500)
		t.drawOn(objeto_canvas, 18, hReal - 730)

		I = ReportBase.create_image(MainParameter.signature, MainParameter.dir_create_file + 'signature.jpg', 160.0, 35.0)
		data = [
				[I if I else '',''],
				[Paragraph('<strong>__________________________</strong>', style_title),
				 Paragraph('<strong>__________________________</strong>', style_title)],
				[Paragraph('<strong>EMPLEADOR</strong>', style_title),
				 Paragraph('<strong>RECIBI CONFORME <br/> TRABAJADOR</strong>', style_title)]
			]
		t = Table(data, [10 * cm, 10 * cm], 3 * [0.5 * cm])
		t.setStyle(TableStyle([
			('ALIGN', (0, 0), (0, 0), 'CENTER'),
			('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
		]))
		t.wrapOn(objeto_canvas, 18, 500)
		t.drawOn(objeto_canvas, 18, hReal - 790)

		objeto_canvas.showPage()

		return objeto_canvas
