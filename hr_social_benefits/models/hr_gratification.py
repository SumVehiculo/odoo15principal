# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError
from datetime import *
import base64, calendar, sys
from math import modf
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, inch, landscape, A4
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_RIGHT, TA_LEFT

class HrGratification(models.Model):
	_name = 'hr.gratification'
	_description = 'Gratification'

	name = fields.Char()
	company_id = fields.Many2one('res.company', string='Compañia', default=lambda self: self.env.company.id, required=True, states={'exported': [('readonly', True)]})
	fiscal_year_id = fields.Many2one('account.fiscal.year', string='Año Fiscal', required=True, states={'exported': [('readonly', True)]})
	with_bonus = fields.Boolean(string='Bono Extraordinario', default=False, states={'exported': [('readonly', True)]})
	months_and_days = fields.Boolean(string='Calcular Dias Grati.', default=False, states={'exported': [('readonly', True)]})
	type = fields.Selection([('07', 'Gratificacion Fiestas Patrias'),
							 ('12', 'Gratificacion Navidad')], string='Tipo Gratificacion', required=True, states={'exported': [('readonly', True)]})
	payslip_run_id = fields.Many2one('hr.payslip.run', string='Periodo', required=True, states={'exported': [('readonly', True)]})
	deposit_date = fields.Date(string='Fecha de Deposito', required=True, states={'exported': [('readonly', True)]})
	line_ids = fields.One2many('hr.gratification.line', 'gratification_id', states={'exported': [('readonly', True)]}, string='Calculo de Gratificacion')
	state = fields.Selection([('draft', 'Borrador'), ('exported', 'Exportado')], default='draft', string='Estado')

	grati_count = fields.Integer(compute='_compute_grati_count')

	def _compute_grati_count(self):
		for grati in self:
			grati.grati_count = len(grati.line_ids)

	def action_open_grati(self):
		self.ensure_one()
		return {
			"type": "ir.actions.act_window",
			"res_model": "hr.gratification.line",
			"views": [[False, "tree"], [False, "form"]],
			"domain": [['id', 'in', self.line_ids.ids]],
			"name": "Boletas Gratificacion",
		}

	def compute_grati_line_all(self):
		self.line_ids.compute_grati_line()
		return self.env['popup.it'].get_message('Se Recalculo exitosamente')

	@api.onchange('fiscal_year_id', 'type')
	def _get_period(self):
		for record in self:
			if record.type and record.fiscal_year_id.name:
				record.name = dict(self._fields['type'].selection).get(record.type) + ' ' + record.fiscal_year_id.name
				date_start = date(int(record.fiscal_year_id.name), int(record.type), 1)
				date_end = date(int(record.fiscal_year_id.name), int(record.type), 31)
				Period = self.env['hr.payslip.run'].search([('date_start', '=', date_start),
															('date_end', '=', date_end)], limit=1)
				if Period:
					record.payslip_run_id = Period.id

	def turn_draft(self):
		self.state = 'draft'

	def set_amounts(self, line_ids, Lot, MainParameter):
		inp_grat = MainParameter.gratification_input_id
		inp_bonus = MainParameter.bonus_nine_input_id
		for line in line_ids:
			Slip = Lot.slip_ids.filtered(lambda slip: slip.employee_id == line.employee_id)
			grat_line = Slip.input_line_ids.filtered(lambda inp: inp.input_type_id == inp_grat)
			bonus_line = Slip.input_line_ids.filtered(lambda inp: inp.input_type_id == inp_bonus)
			grat_line.amount = line.total_grat
			bonus_line.amount = line.bonus_essalud

	def export_gratification(self):
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		MainParameter.check_gratification_values()
		Lot = self.payslip_run_id
		self.set_amounts(self.line_ids, Lot, MainParameter)
		self.state = 'exported'
		return self.env['popup.it'].get_message('Se exporto exitosamente')

	def get_gratification(self):
		# self.line_ids.unlink()
		self.line_ids.filtered(lambda sr: sr.gratification_id.id == self.id and sr.preserve_record == False).unlink()
		self.env['hr.main.parameter'].compute_benefits(self, self.type)
		preservados = self.env['hr.gratification.line'].search(
			[('gratification_id', '=', self.id), ('preserve_record', '=', True)])
		empleados_pre = []
		for j in preservados:
			if j.employee_id.id not in empleados_pre:
				empleados_pre.append(j.employee_id.id)
		eliminar = []
		for l in self.line_ids:
			if l.employee_id.id in empleados_pre:
				if l.preserve_record == False:
					eliminar.append(l)
		for l in eliminar:
			l.unlink()
		return self.env['popup.it'].get_message('Se calculo exitosamente')

	def get_excel_gratification(self):
		import io
		from xlsxwriter.workbook import Workbook
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		route = MainParameter.dir_create_file
		type = dict(self._fields['type'].selection).get(self.type)

		if not route:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Nomina para su Compañía')
		doc_name = '%s %s.xlsx' % (type, self.fiscal_year_id.name)
		workbook = Workbook(route + doc_name)
		
		self.get_gratification_sheet(workbook, self.line_ids)

		workbook.close()
		f = open(route + doc_name, 'rb')
		return self.env['popup.it'].get_file(doc_name, base64.encodebytes(b''.join(f.readlines())))

	def get_gratification_sheet(self, workbook, lines, liquidation=False):
		ReportBase = self.env['report.base']
		workbook, formats = ReportBase.get_formats(workbook)
		labor_regime = dict(self.env['hr.contract']._fields['labor_regime'].selection)

		import importlib
		import sys
		importlib.reload(sys)

		worksheet = workbook.add_worksheet('GRATIFICACION')
		worksheet.set_tab_color('blue')

		#### I'm separating this array of headers 'cause i need a dynamic limiter to set the totals at the end of the printing, i will use the HEADER variable to get the lenght and this will be my limiter'
		HEADERS = ['NRO. DOCUMENTO', 'APELLIDO MATERNO', 'APELLIDO PATERNO', 'NOMBRES', 'FECHA INGRESO', 'REGIMEN LABORAL','DISTRIBUCION ANALITICA', 'SEGURO', 'MES', 'DIAS','FALTAS']
		if liquidation:
			HEADERS = HEADERS[:5] + ['FECHA DE COMPUTO', 'FECHA DE CESE'] + HEADERS[5:]
		HEADERS_WITH_TOTAL = ['SUELDO', 'ASIGNACION FAMILIAR', 'PROMEDIO COMISION', 'PROMEDIO BONIFICACION', 'PROMEDIO HRS EXTRAS', 'REMUNERACION COMPUTABLE',
							  'MONTO POR MES', 'MONTO POR DIA', 'TOTAL FALTAS S/.', 'GRAT. POR MESES', 'GRAT. POR DIAS', 'TOTAL GRAT.', 'BONIFICACION 9%', 'TOTAL A PAGAR']
		
		worksheet = ReportBase.get_headers(worksheet, HEADERS + HEADERS_WITH_TOTAL, 0, 0, formats['boldbord'])
		x, y = 1, 0
		totals = [0] * len(HEADERS_WITH_TOTAL)
		limiter = len(HEADERS)

		for line in lines:

			worksheet.write(x, 0, line.identification_id or '', formats['especial1'])
			worksheet.write(x, 1, line.last_name or '', formats['especial1'])
			worksheet.write(x, 2, line.m_last_name or '', formats['especial1'])
			worksheet.write(x, 3, line.names or '', formats['especial1'])
			worksheet.write(x, 4, line.admission_date or '', formats['reverse_dateformat'])
			if liquidation:
				worksheet.write(x, 5, line.compute_date or '', formats['reverse_dateformat'])
				worksheet.write(x, 6, line.cessation_date or '', formats['reverse_dateformat'])
				y = 2
			worksheet.write(x, 5 + y, labor_regime.get(line.labor_regime) or '', formats['especial1'])
			worksheet.write(x, 6 + y, line.distribution_id or '', formats['especial1'])
			worksheet.write(x, 7 + y, line.social_insurance_id.name or '', formats['especial1'])
			worksheet.write(x, 8 + y, line.months or 0, formats['number'])
			worksheet.write(x, 9 + y, line.days or 0, formats['number'])
			worksheet.write(x, 10 + y, line.lacks or 0, formats['number'])
			worksheet.write(x, 11 + y, line.wage or 0, formats['numberdos'])
			worksheet.write(x, 12 + y, line.household_allowance or 0, formats['numberdos'])
			worksheet.write(x, 13 + y, line.commission or 0, formats['numberdos'])
			worksheet.write(x, 14 + y, line.bonus or 0, formats['numberdos'])
			worksheet.write(x, 15 + y, line.extra_hours or 0, formats['numberdos'])
			worksheet.write(x, 16 + y, line.computable_remuneration or 0, formats['numberdos'])
			worksheet.write(x, 17 + y, line.amount_per_month or 0, formats['numberdos'])
			worksheet.write(x, 18 + y, line.amount_per_day or 0, formats['numberdos'])
			worksheet.write(x, 19 + y, line.amount_per_lack or 0, formats['numberdos'])
			worksheet.write(x, 20 + y, line.grat_per_month or 0, formats['numberdos'])
			worksheet.write(x, 21 + y, line.grat_per_day or 0, formats['numberdos'])
			worksheet.write(x, 22 + y, line.total_grat or 0, formats['numberdos'])
			worksheet.write(x, 23 + y, line.bonus_essalud or 0, formats['numberdos'])
			worksheet.write(x, 24 + y, line.total or 0, formats['numberdos'])

			totals[0] += line.wage
			totals[1] += line.household_allowance
			totals[2] += line.commission
			totals[3] += line.bonus
			totals[4] += line.extra_hours
			totals[5] += line.computable_remuneration
			totals[6] += line.amount_per_month
			totals[7] += line.amount_per_day
			totals[8] += line.amount_per_lack
			totals[9] += line.grat_per_month
			totals[10] += line.grat_per_day
			totals[11] += line.total_grat
			totals[12] += line.bonus_essalud
			totals[13] += line.total

			x += 1
		x += 1
		for total in totals:
			worksheet.write(x, limiter, total, formats['numbertotal'])
			limiter += 1

		widths = [13, 13, 13, 20, 10, 15,15, 8, 5, 5, 8, 8, 13, 11, 16, 13, 16, 9, 9, 12, 11, 11, 8, 19, 10]
		if liquidation:
			widths = widths[:5] + [10, 10] + widths[5:]
		worksheet = ReportBase.resize_cells(worksheet, widths)

	def grati_by_lot(self):
		if len(self.ids) > 1:
			raise UserError('No se puede seleccionar mas de un registro para este proceso')
		return self.env['hr.gratification.line'].get_vouchers_grati(self.line_ids)

class HrGratificationLine(models.Model):
	_name = 'hr.gratification.line'
	_description = 'Gratification Line'
	_order = 'employee_id'

	liquidation_id = fields.Many2one('hr.liquidation', ondelete='cascade', string='Periodo')
	gratification_id = fields.Many2one('hr.gratification', ondelete='cascade')
	employee_id = fields.Many2one('hr.employee', string='Empleado')
	contract_id = fields.Many2one('hr.contract', string='Contrato')
	identification_id = fields.Char(related='employee_id.identification_id', string='Nro Documento')
	last_name = fields.Char(related='employee_id.last_name', string='Apellido Paterno')
	m_last_name = fields.Char(related='employee_id.m_last_name', string='Apellido Materno')
	names = fields.Char(related='employee_id.names', string='Nombres')
	admission_date = fields.Date(string='Fecha de Ingreso')
	compute_date = fields.Date(string='Fecha de Computo')
	cessation_date = fields.Date(string='Fecha de Cese')
	labor_regime = fields.Selection(related='contract_id.labor_regime', string='Regimen Laboral')
	social_insurance_id = fields.Many2one(related='contract_id.social_insurance_id', string='Seguro Social')
	distribution_id = fields.Char(string='Distribucion Analitica')
	months = fields.Integer(string='Meses')
	days = fields.Integer(string='Dias')
	lacks = fields.Integer(string='Faltas')
	wage = fields.Float(string='Sueldo')
	household_allowance = fields.Float(string='Asignacion Familiar')
	commission = fields.Float(string='Prom. Comision')
	bonus = fields.Float(string='Prom. Bonificacion')
	extra_hours = fields.Float(string='Prom. Horas Extras')
	computable_remuneration = fields.Float(string='Remuneracion Computable')
	amount_per_month = fields.Float(string='Monto por Mes')
	amount_per_day = fields.Float(string='Monto por Dia')
	amount_per_lack = fields.Float(string='(-) Monto por Faltas')
	grat_per_month = fields.Float(string='Grat. por Meses')
	grat_per_day = fields.Float(string='Grat. por Dias')
	total_grat = fields.Float(string='Total Grat.')
	bonus_essalud = fields.Float(string='(+) Bono Extra.')
	total = fields.Float(string='Total a Pagar')

	preserve_record = fields.Boolean('No Recalcular')

	def compute_grati_line(self):
		ReportBase = self.env['report.base']
		# self.env['hr.gratification.line'].search([('gratification_id', '=', None), ('id', 'not in', self.ids)]).unlink()

		for record in self:
			record.computable_remuneration = record.wage + record.household_allowance + record.commission + record.bonus + record.extra_hours
			record.amount_per_month = record.computable_remuneration/6 if record.contract_id.labor_regime == 'general' else record.computable_remuneration/12
			record.amount_per_day = record.amount_per_month/30
			record.amount_per_lack = record.amount_per_day * record.lacks
			record.grat_per_month = ReportBase.custom_round(record.amount_per_month * record.months, 2)
			record.grat_per_day = ReportBase.custom_round(record.amount_per_day * record.days, 2)
			record.total_grat = ReportBase.custom_round((record.grat_per_month + record.grat_per_day) - record.amount_per_lack, 2)
			# percent = record.contract_id.social_insurance_id.percent or 0 if self.gratification_id.with_bonus else 0
			if record.gratification_id:
				percent = record.social_insurance_id.percent or 0 if record.gratification_id.with_bonus else 0
				# print("percent grati",percent)
			elif record.liquidation_id:
				percent = record.social_insurance_id.percent or 0 if record.liquidation_id.with_bonus else 0
				# print("percent liqui",percent)
			record.bonus_essalud = ReportBase.custom_round(record.total_grat * percent * 0.01, 2)
			record.total = ReportBase.custom_round(record.total_grat + record.bonus_essalud, 2)
			if not record.total > 0 and not self._context.get('line_form', False):
				record.unlink()

	def send_grati_by_email(self):
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		route = MainParameter.dir_create_file + 'BOLETA DE GRATIFICACION.pdf'
		issues = []
		for payslip in self:
			Employee = payslip.employee_id
			doc = SimpleDocTemplate(route, pagesize=letter,
									rightMargin=30,
									leftMargin=30,
									topMargin=30,
									bottomMargin=20,
									encrypt=Employee.identification_id)
			doc.build(payslip.get_pdf_grati())
			f = open(route, 'rb')
			try:
				self.env['mail.mail'].create({
					'subject': 'Boleta: %s %s' % (
					dict(payslip.gratification_id._fields['type'].selection).get(payslip.gratification_id.type),
					payslip.gratification_id.fiscal_year_id.name),
					'body_html': 'Estimado (a) %s,<br/>'
								 'Estamos adjuntando su boleta de %s %s,<br/>'
								 '<strong>Nota: Para abrir su boleta es necesario colocar su dni como clave</strong>' % (
								 Employee.name, dict(payslip.gratification_id._fields['type'].selection).get(
									 payslip.gratification_id.type), payslip.gratification_id.fiscal_year_id.name),
					'email_to': Employee.work_email,
					'attachment_ids': [(0, 0, {'name': 'Boleta Gratificacion %s.pdf' % Employee.name,
											   'datas': base64.encodebytes(b''.join(f.readlines()))}
										)]
				}).send()
				f.close()
			except:
				issues.append(Employee.name)
		if issues:
			return self.env['popup.it'].get_message(
				'No se pudieron enviar las boletas de los siguientes Empleados: \n %s' % '\n'.join(issues))
		else:
			return self.env['popup.it'].get_message(
				'Se enviaron todas las boletas de gratificacion satisfactoriamente.')

	def get_vouchers_grati(self, payslips=None):
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		# if not MainParameter.employee_in_charge_id:
		# 	raise UserError('Falta configurar un Encargado para Liquidacion Semestral en Parametros Principales en la Pestaña de CTS')
		route = MainParameter.dir_create_file
		doc = SimpleDocTemplate(route + "BOLETA DE GRATIFICACION.pdf", pagesize=A4, topMargin=20, bottomMargin=20)
		elements = []
		# print("payslips",payslips)
		if payslips:
			for payslip in payslips:
				elements += payslip.get_pdf_grati()
		else:
			elements += self.get_pdf_grati()
		doc.build(elements)
		f = open(route + 'BOLETA DE GRATIFICACION.pdf', 'rb')
		return self.env['popup.it'].get_file('BOLETA DE GRATIFICACION.pdf', base64.encodebytes(b''.join(f.readlines())))

	def get_pdf_grati(self):
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		MainParameter.check_voucher_values()
		ReportBase = self.env['report.base']
		Employee = self.employee_id
		Contract = self.contract_id
		admission_date = self.env['hr.contract'].get_first_contract(Employee, Contract).date_start
		year = int(self.gratification_id.fiscal_year_id.name)

		if not MainParameter.dir_create_file:
			raise UserError(
				u'No existe un Directorio de Descarga configurado en Parametros Principales de Nomina para su Compañía')
		elements = []
		style_title = ParagraphStyle(name='Center', alignment=TA_CENTER, fontSize=12, fontName="times-roman")
		style_cell = ParagraphStyle(name='Center', alignment=TA_CENTER, fontSize=9.6, fontName="times-roman")
		style_right = ParagraphStyle(name='Center', alignment=TA_RIGHT, fontSize=9.6, fontName="times-roman")
		style_left = ParagraphStyle(name='Center', alignment=TA_LEFT, fontSize=9.6, fontName="times-roman")
		style_center = ParagraphStyle(name='Center', alignment=TA_CENTER, fontSize=9, fontName="times-roman")
		style_left_title = ParagraphStyle(name='Center', alignment=TA_LEFT, fontSize=11, fontName="times-roman")
		internal_width = [2.5 * cm]
		simple_style = [('ALIGN', (0, 0), (-1, -1), 'CENTER'),
						('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]
		bg_color = colors.HexColor("#FFB6C1")
		spacer = Spacer(10, 20)

		I = ReportBase.create_image(self.env.company.logo, MainParameter.dir_create_file + 'logo.jpg', 110.0, 80.0)
		data = [
			[I if I else '',
			 Paragraph('<strong>DECRETO SUPREMO N° 007-2009-TR LEY BASE N° 29351\
		                 Y LEY PRORROGA 29714</strong>', style_cell),
			 Paragraph('<strong>R.U.C. %s </strong>' % self.env.company.vat or '', style_cell)],
			['', Paragraph('<strong>%s</strong>' % self.env.company.name or '', style_title),
			 Paragraph('<strong>BOLETA DE GRATIFICACION</strong>', style_title)],
			['', Paragraph(self.env.company.street or '', style_cell),
			 Paragraph('<strong>R08: Trabajador</strong>', style_cell)],
			['', '', '']
		]
		t = Table(data, [4 * cm, 10 * cm, 6 * cm])
		t.setStyle(TableStyle([
			('SPAN', (0, 0), (0, -1)),
			('SPAN', (2, 2), (-1, -1)),
			('ALIGN', (0, 0), (0, 0), 'CENTER'),
			('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
			('BACKGROUND', (2, 1), (2, 1), bg_color),
			('BOX', (2, 0), (-1, -1), 0.25, colors.black)]))
		elements.append(t)
		elements.append(spacer)

		data = [
			[Paragraph('%s %d' % (
			dict(self.gratification_id._fields['type'].selection).get(self.gratification_id.type) or '', year or ''),
					   style_left_title),
			 Paragraph('Fecha de Pago: %s' % datetime.strftime((self.gratification_id.deposit_date),'%d-%m-%Y') or '', style_cell)],
		]
		t = Table(data, [14 * cm, 6 * cm], [1 * cm])
		t.setStyle(TableStyle([
			('BACKGROUND', (0, 0), (-1, -1), bg_color),
			('ALIGN', (0, 0), (-1, -1), 'CENTER'),
			('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
			('BOX', (0, 0), (-1, -1), 0.25, colors.black)
		]))
		elements.append(t)
		elements.append(spacer)

		if Contract.situation_id.name == 'BAJA':
			if self.gratification_id.payslip_run_id.date_start <= Contract.date_end <= self.gratification_id.payslip_run_id.date_end:
				situacion = 'BAJA'
			else:
				situacion = 'ACTIVO O SUBSIDIADO'
		else:
			situacion = 'ACTIVO O SUBSIDIADO'
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
			 Paragraph('Regimen Laboral', style_cell), '',
			 Paragraph('CUSPP', style_cell), ''],
			[Paragraph(str(datetime.strftime((admission_date),'%d-%m-%Y')) or '', style_cell), '',
			 Paragraph(Contract.worker_type_id.name or '', style_cell), '',
			 Paragraph(dict(Contract._fields['labor_regime'].selection).get(Contract.labor_regime) or '', style_cell),
			 '',
			 Paragraph(Contract.cuspp or '', style_cell), '']
		]
		second_row_format = [
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
			[Paragraph(u'Periodo Computable', style_cell), '',
			 Paragraph(u'Total Meses', style_cell),
			 Paragraph(u'Condición', style_cell),
			 Paragraph('Jornada Ordinaria', style_cell), '',
			 Paragraph('Remumeracion Computable', style_cell), ''],
			['', '', '', '',
			 Paragraph('Total Horas', style_cell),
			 Paragraph('Minutos', style_cell),
			 Paragraph('Seguro Social', style_cell),
			 Paragraph('Importe', style_cell)],
			[Paragraph('%s' % ('01/01/%d al 30/06/%d' % (
			year, year) if self.gratification_id.type == '07' else '01/07/%d al 31/12/%d' % (year, year)), style_cell),
			 '',
			 Paragraph('%d' % self.months or '0', style_cell),
			 Paragraph(dict(Employee._fields['condition'].selection).get(Employee.condition) or '', style_cell),
			 Paragraph('', style_cell),
			 Paragraph('', style_cell),
			 Paragraph(self.social_insurance_id.name if self.social_insurance_id else '', style_cell),
			 Paragraph('{:,.2f}'.format(self.computable_remuneration) or '0.00', style_cell)]
		]
		third_row_format = [
			('SPAN', (0, 5), (1, 6)),
			('SPAN', (0, 7), (1, 7)),
			('SPAN', (2, 5), (2, 6)),
			('SPAN', (3, 5), (3, 6)),
			('SPAN', (4, 5), (5, 5)),
			('SPAN', (6, 5), (7, 5)),
			('BACKGROUND', (0, 5), (-1, 6), bg_color)
		]
		global_format = [
			('ALIGN', (0, 0), (-1, -1), 'CENTER'),
			('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
			('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
			('BOX', (0, 0), (-1, -1), 0.25, colors.black)
		]

		t = Table(first_row + second_row + third_row, 8 * internal_width, 8 * [0.5 * cm])
		t.setStyle(TableStyle(first_row_format + second_row_format + third_row_format + global_format))
		elements.append(t)
		elements.append(spacer)

		data = [[
			Paragraph(u'Código', style_cell),
			Paragraph('Conceptos', style_cell),
			Paragraph('Ingresos S/.', style_cell),
			Paragraph('Descuentos S/.', style_cell),
			Paragraph('Neto S/.', style_cell)
		]]
		data_format = [('BACKGROUND', (0, 0), (-1, 0), bg_color)]

		# Ingresos
		data += [[Paragraph('Ingresos', style_left), '', '', '', '']]

		data_format += [('SPAN', (0, 1), (-1, 1)),
						('BACKGROUND', (0, 1), (-1, 1), bg_color)]
		data += [[
			Paragraph('0406', style_left),
			Paragraph('Gratificacion Ley 29351 y 30334', style_left),
			Paragraph('{:,.2f}'.format(self.total_grat) or '0.00', style_right),
			'', ''],
			[
				Paragraph('0312', style_left),
				Paragraph('Bonificacion Extraordinaria', style_left),
				Paragraph('{:,.2f}'.format(self.bonus_essalud) or '0.00', style_right),
				'', ''
			]]
		# Descuentos
		data += [[Paragraph('Descuentos', style_left), '', '', '', '']]

		data_format += [('SPAN', (0, 4), (-1, 4)),
						('BACKGROUND', (0, 4), (-1, 4), bg_color)]
		# data += [[
		# 	Paragraph('0701', style_left),
		# 	Paragraph('Adelanto de Gratificacion', style_left), '',
		# 	Paragraph('{:,.2f}'.format(self.advance_amount) or '0.00', style_right),
		# 	'']]

		data += [[Paragraph('Neto a Pagar', style_left), '', '', '',
				  Paragraph('{:,.2f}'.format(self.total) or '0.00', style_right)]]
		data_format += [
			('SPAN', (0, -1), (3, -1)),
			('BACKGROUND', (0, -1), (-1, -1), bg_color),
			('ALIGN', (0, 0), (-1, -1), 'CENTER'),
			('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
			('INNERGRID', (0, 0), (-1, 0), 0.25, colors.black),
			('BOX', (0, 0), (-1, 0), 0.25, colors.black),
			('BOX', (0, 0), (-1, -1), 0.25, colors.black)
		]
		t = Table(data, [3 * cm, 8 * cm, 3 * cm, 3 * cm, 3 * cm], len(data) * [0.5 * cm])
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