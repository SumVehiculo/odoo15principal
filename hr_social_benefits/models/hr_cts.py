# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError
from datetime import *
import base64, calendar, sys
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, inch, landscape, A4
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_RIGHT, TA_LEFT

class HrCts(models.Model):
	_name = 'hr.cts'
	_description = 'Hr Cts'

	name = fields.Char()
	company_id = fields.Many2one('res.company', string='Compañia', default=lambda self: self.env.company.id, required=True, states={'exported': [('readonly', True)]})
	fiscal_year_id = fields.Many2one('account.fiscal.year', string='Año Fiscal', required=True, states={'exported': [('readonly', True)]})
	exchange_type = fields.Float(string='Tipo de Cambio', default=1, states={'exported': [('readonly', True)]})
	type = fields.Selection([('11', 'CTS Mayo - Octubre'),
							 ('05', 'CTS Noviembre - Abril')], string='Tipo CTS', required=True, states={'exported': [('readonly', True)]})
	payslip_run_id = fields.Many2one('hr.payslip.run', string='Periodo', required=True, states={'exported': [('readonly', True)]})
	deposit_date = fields.Date(string='Fecha de Deposito', required=True, states={'exported': [('readonly', True)]})
	line_ids = fields.One2many('hr.cts.line', 'cts_id', states={'exported': [('readonly', True)]}, string='Calculo de CTS')
	state = fields.Selection([('draft', 'Borrador'), ('exported', 'Exportado')], default='draft', string='Estado')

	cts_count = fields.Integer(compute='_compute_cts_count')

	def _compute_cts_count(self):
		for cts in self:
			cts.cts_count = len(cts.line_ids.filtered(lambda line: not line.less_than_one_month))

	def action_open_cts(self):
		self.ensure_one()
		return {
			"type": "ir.actions.act_window",
			"res_model": "hr.cts.line",
			"views": [[False, "tree"], [False, "form"]],
			"domain": [['id', 'in', self.line_ids.filtered(lambda line: not line.less_than_one_month).ids]],
			"name": "Certificados CTS",
		}

	def compute_cts_line_all(self):
		self.line_ids.compute_cts_line()
		return self.env['popup.it'].get_message('Se Recalculo exitosamente')

	@api.onchange('fiscal_year_id', 'type')
	def _get_period(self):
		for record in self:
			if record.type and record.fiscal_year_id.name:
				type = dict(self._fields['type'].selection).get(record.type)
				year = int(record.fiscal_year_id.name)
				record.name = '%s %d' % (type, year)
				_, last_day = calendar.monthrange(year, int(record.type))
				date_start = date(year, int(record.type), 1)
				date_end = date(year, int(record.type), last_day)
				Period = self.env['hr.payslip.run'].search([('date_start', '=', date_start),
															('date_end', '=', date_end)], limit=1)
				if Period:
					record.payslip_run_id = Period.id

	def turn_draft(self):
		self.state = 'draft'

	def set_amounts(self, line_ids, Lot, MainParameter):
		inp_cts = MainParameter.cts_input_id
		for line in line_ids.filtered(lambda linea: not linea.less_than_one_month):
			Slip = Lot.slip_ids.filtered(lambda slip: slip.employee_id == line.employee_id)
			cts_line = Slip.input_line_ids.filtered(lambda inp: inp.input_type_id == inp_cts)
			cts_line.amount = line.total_cts

	def export_cts(self):
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		MainParameter.check_cts_values()
		Lot = self.payslip_run_id
		self.set_amounts(self.line_ids, Lot, MainParameter)
		self.state = 'exported'
		return self.env['popup.it'].get_message('Se exporto exitosamente')

	def get_cts(self):
		# self.line_ids.unlink()
		self.line_ids.filtered(lambda sr: sr.cts_id.id == self.id and sr.preserve_record == False).unlink()
		self.env['hr.main.parameter'].compute_benefits(self, self.type)
		preservados = self.env['hr.cts.line'].search([('cts_id', '=', self.id), ('preserve_record', '=', True)])
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

	def get_excel_cts(self):
		import io
		from xlsxwriter.workbook import Workbook
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		route = MainParameter.dir_create_file
		type = dict(self._fields['type'].selection).get(self.type)

		if not route:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Nomina para su Compañía')
		doc_name = '%s %s.xlsx' % (type, self.fiscal_year_id.name)
		workbook = Workbook(route + doc_name)
		
		self.get_cts_sheet(workbook, self.line_ids)

		workbook.close()
		f = open(route + doc_name, 'rb')
		return self.env['popup.it'].get_file(doc_name, base64.encodebytes(b''.join(f.readlines())))

	def get_cts_sheet(self, workbook, lines, liquidation=False):
		ReportBase = self.env['report.base']
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		worksheet = workbook.add_worksheet('CTS')
		worksheet.set_tab_color('green')

		HEADERS = ['NRO. DOCUMENTO', 'APELLIDO MATERNO', 'APELLIDO PATERNO', 'NOMBRES', 'FECHA INGRESO', 'CUENTA CTS', 'BANCO', 'TIPO DE CAMBIO','DISTRIBUCION ANALITICA', 'MES', 'DIAS','FALTAS']
		if liquidation:
			HEADERS = HEADERS[:5] + ['FECHA DE COMPUTO', 'FECHA DE CESE'] + HEADERS[5:]
		HEADERS_WITH_TOTAL = ['SUELDO', 'ASIGNACION FAMILIAR', '1/6 GRATIFICACION', 'PROMEDIO COMISION', 'PROMEDIO BONIFICACION', 'PROMEDIO HRS EXTRAS',
							  'REMUNERACION COMPUTABLE','MONTO POR MES', 'MONTO POR DIA', 'TOTAL FALTAS S/.', 'CTS SOLES POR MESES', 'CTS SOLES POR DIAS', 
							  'CTS SOLES', 'INTERES CTS', 'OTROS DESCUENTOS', 'CTS A PAGAR', 'CTS DOLARES']

		worksheet = ReportBase.get_headers(worksheet, HEADERS + HEADERS_WITH_TOTAL, 0, 0, formats['boldbord'])
		x, y = 1, 0
		totals = [0] * len(HEADERS_WITH_TOTAL)
		limiter = len(HEADERS)
		for line in lines.filtered(lambda line: not line.less_than_one_month):
			worksheet.write(x, 0, line.identification_id or '', formats['especial1'])
			worksheet.write(x, 1, line.last_name or '', formats['especial1'])
			worksheet.write(x, 2, line.m_last_name or '', formats['especial1'])
			worksheet.write(x, 3, line.names or '', formats['especial1'])
			worksheet.write(x, 4, line.admission_date or '', formats['reverse_dateformat'])
			if liquidation:
				worksheet.write(x, 5, line.compute_date or '', formats['reverse_dateformat'])
				worksheet.write(x, 6, line.cessation_date or '', formats['reverse_dateformat'])
				y = 2
			worksheet.write(x, 5 + y, line.cts_account.acc_number or '', formats['especial1'])
			worksheet.write(x, 6 + y, line.cts_bank.name or '', formats['especial1'])
			worksheet.write(x, 7 + y, line.exchange_type or 1, formats['numberdos'])
			worksheet.write(x, 8 + y, line.distribution_id or '', formats['especial1'])
			worksheet.write(x, 9 + y, line.months or 0, formats['number'])
			worksheet.write(x, 10 + y, line.days or 0, formats['number'])
			worksheet.write(x, 11 + y, line.lacks or 0, formats['number'])
			worksheet.write(x, 12 + y, line.wage or 0, formats['numberdos'])
			worksheet.write(x, 13 + y, line.household_allowance or 0, formats['numberdos'])
			worksheet.write(x, 14 + y, line.sixth_of_gratification or 0, formats['numberdos'])
			worksheet.write(x, 15 + y, line.commission or 0, formats['numberdos'])
			worksheet.write(x, 16 + y, line.bonus or 0, formats['numberdos'])
			worksheet.write(x, 17 + y, line.extra_hours or 0, formats['numberdos'])
			worksheet.write(x, 18 + y, line.computable_remuneration or 0, formats['numberdos'])
			worksheet.write(x, 19 + y, line.amount_per_month or 0, formats['numberdos'])
			worksheet.write(x, 20 + y, line.amount_per_day or 0, formats['numberdos'])
			worksheet.write(x, 21 + y, line.amount_per_lack or 0, formats['numberdos'])
			worksheet.write(x, 22 + y, line.cts_per_month or 0, formats['numberdos'])
			worksheet.write(x, 23 + y, line.cts_per_day or 0, formats['numberdos'])
			worksheet.write(x, 24 + y, line.cts_soles or 0, formats['numberdos'])
			worksheet.write(x, 25 + y, line.cts_interest or 0, formats['numberdos'])
			worksheet.write(x, 26 + y, line.other_discounts or 0, formats['numberdos'])
			worksheet.write(x, 27 + y, line.total_cts or 0, formats['numberdos'])
			worksheet.write(x, 28 + y, line.cts_dollars or 0, formats['numberdos'])

			totals[0] += line.wage
			totals[1] += line.household_allowance
			totals[2] += line.sixth_of_gratification
			totals[3] += line.commission
			totals[4] += line.bonus
			totals[5] += line.extra_hours
			totals[6] += line.computable_remuneration
			totals[7] += line.amount_per_month
			totals[8] += line.amount_per_day
			totals[9] += line.amount_per_lack
			totals[10] += line.cts_per_month
			totals[11] += line.cts_per_day
			totals[12] += line.cts_soles
			totals[13] += line.cts_interest
			totals[14] += line.other_discounts
			totals[15] += line.total_cts
			totals[16] += line.cts_dollars

			x += 1
		x += 1
		for total in totals:
			worksheet.write(x, limiter, total, formats['numbertotal'])
			limiter += 1

		widths = [13, 13, 13, 20, 10, 16, 14,  9, 15,  5,  5,
				   8,  8, 14, 17, 11, 16, 13, 16,  9,  9,
				  12, 12, 11,  9, 13, 13,  9, 10]
		if liquidation:
			widths = widths[:5] + [10, 10] + widths[5:]
		worksheet = ReportBase.resize_cells(worksheet, widths)

	def cts_by_lot(self):
		if len(self.ids) > 1:
			raise UserError('No se puede seleccionar mas de un registro para este proceso')
		return self.env['hr.cts.line'].get_vouchers_cts(self.line_ids)


class HrCtsLine(models.Model):
	_name = 'hr.cts.line'
	_description = 'Hr Cts Line'
	_order = 'employee_id'

	liquidation_id = fields.Many2one('hr.liquidation', ondelete='cascade')
	cts_id = fields.Many2one('hr.cts', ondelete='cascade')
	employee_id = fields.Many2one('hr.employee', string='Empleado')
	contract_id = fields.Many2one('hr.contract', string='Contrato')
	less_than_one_month = fields.Boolean(default=False)
	identification_id = fields.Char(related='employee_id.identification_id', string='Nro Documento')
	last_name = fields.Char(related='employee_id.last_name', string='Apellido Paterno')
	m_last_name = fields.Char(related='employee_id.m_last_name', string='Apellido Materno')
	names = fields.Char(related='employee_id.names', string='Nombres')
	admission_date = fields.Date(string='Fecha de Ingreso')
	compute_date = fields.Date(string='Fecha de Computo')
	cessation_date = fields.Date(string='Fecha de Cese')
	cts_account = fields.Many2one(related='employee_id.cts_bank_account_id', string='Cuenta CTS')
	cts_bank = fields.Many2one(related='cts_account.bank_id', string='Banco')
	exchange_type = fields.Float(string='Tipo de Cambio')
	distribution_id = fields.Char(string='Distribucion Analitica')
	months = fields.Integer(string='Meses')
	days = fields.Integer(string='Dias')
	lacks = fields.Integer(string='Faltas')
	excess_medical_rest = fields.Integer(string='Exceso Descanso Medico')
	wage = fields.Float(string='Sueldo')
	household_allowance = fields.Float(string='Asignacion Familiar')
	sixth_of_gratification = fields.Float(string='1/6 Gratificacion')
	commission = fields.Float(string='Prom. Comision')
	bonus = fields.Float(string='Prom. Bonificacion')
	extra_hours = fields.Float(string='Prom. Horas Extras')
	computable_remuneration = fields.Float(string='Remuneracion Computable')
	amount_per_month = fields.Float(string='Monto por Mes')
	amount_per_day = fields.Float(string='Monto por Dia')
	amount_per_lack = fields.Float(string='(-) Monto por Faltas')
	cts_per_month = fields.Float(string='CTS por Meses')
	cts_per_day = fields.Float(string='CTS por Dias')
	cts_interest = fields.Float(string='(+) Interes CTS')
	other_discounts = fields.Float(string='(-) Otros Descuentos')
	total_cts = fields.Float(string='Total CTS')
	cts_soles = fields.Float(string='CTS a Pagar Soles')
	cts_dollars = fields.Float(string='CTS a Pagar Dolares')

	preserve_record = fields.Boolean('No Recalcular')

	# @api.onchange('cts_interest', 'other_discounts')
	# def get_total_cts(self):
	# 	for record in self:
	# 		record.total_cts = record.cts_soles + record.cts_interest - record.other_discounts
	# 		record.cts_dollars = self.env['report.base'].custom_round(record.total_cts/record.exchange_type, 2)

	def compute_cts_line(self):
		ReportBase = self.env['report.base']
		# self.env['hr.cts.line'].search([('cts_id', '=', None), ('id', 'not in', self.ids)]).unlink()

		for record in self:
			record.computable_remuneration = record.wage + record.household_allowance + record.sixth_of_gratification + record.commission + record.bonus + record.extra_hours
			record.amount_per_month = record.computable_remuneration/12 if record.contract_id.labor_regime == 'general' else record.computable_remuneration/24
			record.amount_per_day = record.amount_per_month/30
			record.amount_per_lack = record.amount_per_day * record.lacks
			record.cts_per_month = ReportBase.custom_round(record.amount_per_month * record.months, 2)
			record.cts_per_day = ReportBase.custom_round(record.amount_per_day * record.days, 2)
			record.total_cts = record.cts_per_month + record.cts_per_day - record.amount_per_lack + record.cts_interest - record.other_discounts
			record.cts_soles = ReportBase.custom_round(record.total_cts, 2)
			record.cts_dollars = ReportBase.custom_round(record.total_cts/record.exchange_type, 2)
			if not record.total_cts > 0 and not self._context.get('line_form', False):
				record.unlink()

	def send_cts_by_email(self):
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		route = MainParameter.dir_create_file + 'LIQUIDACION DE DEPOSITO SEMESTRAL CTS.pdf'
		issues = []
		for payslip in self:
			Employee = payslip.employee_id
			doc = SimpleDocTemplate(route, pagesize=letter,
				rightMargin=30,
				leftMargin=30,
				topMargin=30,
				bottomMargin=20,
				encrypt=Employee.identification_id)
			doc.build(payslip.get_pdf_cts())
			f = open(route, 'rb')
			try:
				self.env['mail.mail'].sudo().create({
						'subject': 'Certificado: %s %s' % (dict(payslip.cts_id._fields['type'].selection).get(payslip.cts_id.type),payslip.cts_id.fiscal_year_id.name),
						'body_html':'Estimado (a) %s,<br/>'
									'Estamos adjuntando su certificado de %s %s,<br/>'
									'<strong>Nota: Para abrir su certificado es necesario colocar su dni como clave</strong>' % (Employee.name, dict(payslip.cts_id._fields['type'].selection).get(payslip.cts_id.type),payslip.cts_id.fiscal_year_id.name),
						'email_to': Employee.work_email,
						'attachment_ids': [(0, 0, {'name': 'Certificado CTS %s.pdf' % Employee.name,
												   'datas': base64.encodebytes(b''.join(f.readlines()))}
										)]
					}).send()
				f.close()
			except:
				issues.append(Employee.name)
		if issues:
			return self.env['popup.it'].get_message('No se pudieron enviar los certificados de los siguientes Empleados: \n %s' % '\n'.join(issues))
		else:
			return self.env['popup.it'].get_message('Se enviaron todas los Certificados de CTS satisfactoriamente.')

	def get_vouchers_cts(self, payslips=None):
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		# if not self.cts_id.deposit_date:
		# 	raise UserError('Necesita especificar una fecha de deposito')
		if not MainParameter.employee_in_charge_id:
			raise UserError('Falta configurar un Encargado para Liquidacion Semestral en Parametros Principales en la Pestaña de CTS')
		route = MainParameter.dir_create_file
		doc = SimpleDocTemplate(route + "LIQUIDACION DE DEPOSITO SEMESTRAL CTS.pdf", pagesize=A4, topMargin=20, bottomMargin=20)
		elements = []
		# print("payslips",payslips)
		if payslips:
			for payslip in payslips.filtered(lambda line: not line.less_than_one_month):
				elements += payslip.get_pdf_cts()
		else:
			elements += self.get_pdf_cts()
		doc.build(elements)
		f = open(route + 'LIQUIDACION DE DEPOSITO SEMESTRAL CTS.pdf', 'rb')
		return self.env['popup.it'].get_file('LIQUIDACION DE DEPOSITO SEMESTRAL CTS.pdf', base64.encodebytes(b''.join(f.readlines())))

	def get_pdf_cts(self):
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		MainParameter.check_voucher_values()
		ReportBase = self.env['report.base']
		if not MainParameter.dir_create_file:
			raise UserError(u'No existe un Directorio de Descarga configurado en Parametros Principales de Nomina para su Compañía')
		elements = []
		# Definiendo los estilos de la cabecera.
		styles = getSampleStyleSheet()
		styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY))
		styles.add(ParagraphStyle(name='Center', alignment=TA_CENTER))
		styles.add(ParagraphStyle(name='LeftBold',
								  fontSize=10,
								  fontName='Times-Bold',

								  ))
		styles.add(ParagraphStyle(name='Left',
								  fontSize=10,
								  fontName='Times-Roman',
								  ))
		styles.add(ParagraphStyle(name='Tab',
								  fontSize=10,
								  fontName='Times-Roman',
								  leftIndent=20,

								  ))
		styles.add(ParagraphStyle(name='RightBold',
								  fontSize=10,
								  fontName='Times-Bold',
								  alignment=TA_RIGHT,
								  ))

		styles.add(ParagraphStyle(name='Right',
								  fontSize=10,
								  alignment=TA_RIGHT,
								  fontName='Times-Roman',
								  ))
		# for line in self.env.ids.filtered(lambda line: not line.less_than_one_month):
		I = ReportBase.create_image(self.env.company.logo, MainParameter.dir_create_file + 'logo.jpg', 150.0, 40.0)
		data = [[I if I else '']]
		t = Table(data, colWidths=[450], rowHeights=[20])
		t.setStyle(TableStyle([('ALIGN', (0, 0), (0, 0), 'LEFT'),
							   ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]))
		elements.append(t)
		elements.append(Spacer(0, 20))

		cadt = [[u'LIQUIDACIÓN DE DEPÓSITO SEMESTRAL DE CTS']]
		t = Table(cadt, colWidths=[450], rowHeights=[20])
		t.setStyle(TableStyle(
			[
				('ALIGN', (0, 0), (-1, -1), 'CENTER'),
				('VALIGN', (0, -1), (-1, -1), 'TOP'),
				('FONTSIZE', (0, 0), (-1, -1), 14),
				('FONT', (0, 0), (-1, -1), 'Helvetica-Bold'),
			]
		))
		elements.append(t)
		elements.append(Spacer(0, 20))
		company = self.env.company
		cts_account = self.employee_id.cts_bank_account_id
		text = u"""<b>{name}</b> con RUC <b>Nº {ruc}</b>, domiciliada en {street},
						representado por su <b>{employee_in_charge} {ec_gender} {ec_name}</b>,
						en aplicación del artículo 24º del TUO del D.Leg Nº 650, Ley de Compensación por Tiempo de
						Servicios, aprobado mediante el D.S. Nº 001-97-TR, otorga a <b>{employee_name}</b>,
						la presente constancia del depósito de su compensación por Tiempo de Servicios realizado 
						el {day} de {month} del {year} en la cuenta CTS {currency}
						<b>Nº {acc_number}</b> del <b>{bank}</b>, por los siguientes montos y periodos:
					""".format(
			name = company.name,
			employee_name= self.employee_id.name,
			ruc = company.vat,
			street = company.street,
			employee_in_charge = MainParameter.employee_in_charge_id.job_id.name or '',
			ec_gender = 'Señor' if MainParameter.employee_in_charge_id.gender == 'male' else 'Señora',
			ec_name = MainParameter.employee_in_charge_id.name,
			day = self.cts_id.deposit_date.day,
			month = MainParameter.get_month_name(self.cts_id.deposit_date.month),
			year = self.cts_id.deposit_date.year,
			currency = '(Dólares Americanos)' if cts_account.currency_id.name == 'USD' else '(Soles)',
			acc_number = cts_account.acc_number or '',
			bank = cts_account.bank_id.name or '',
		)
		elements.append(Paragraph(text, styles["Justify"]))
		period = ''
		year = int(self.cts_id.fiscal_year_id.name)
		if self.cts_id.type == '11':
			period = 'Del 01 de Mayo del {year} al 31 de Octubre del {year}'.format(year = year)
		else:
			period = 'Del 01 de Noviembre {last_year} del al 30 de Abril del {year}'.format(last_year = year - 1, year = year)
		period += u': {months} meses, {days} días'.format(months = self.months, days = self.days)
		datat = [
			[Paragraph('<b>1. <u>FECHA DE INGRESO</u>: </b> %s' % self.admission_date.strftime('%d/%m/%Y'), styles["Left"]), '', ''],
			[Paragraph('2. <u>PERIODO QUE SE LIQUIDA</u>:', styles["LeftBold"]), '', ''],
			[Paragraph(period, styles["Tab"]), '', ''],
			[Paragraph('3. <u>REMUNERACION COMPUTABLE</u>:', styles["LeftBold"]), '', ''],
			[Paragraph('-  Básico', styles["Tab"]), 'S/.', Paragraph('{:,.2f}'.format(self.wage or 0.00), styles["Right"])],
			[Paragraph('-  Asignación Familiar', styles["Tab"]), 'S/.', Paragraph('{:,.2f}'.format(self.household_allowance or 0.00), styles["Right"])],
			[Paragraph('-  1/6 de Gratificacion', styles["Tab"]), 'S/.', Paragraph('{:,.2f}'.format(self.sixth_of_gratification or 0.00), styles["Right"])],
			[Paragraph('-  Prom Horas Extra', styles["Tab"]), 'S/.', Paragraph('{:,.2f}'.format(self.extra_hours or 0.00), styles["Right"])],
			[Paragraph('-  Prom Bonificación', styles["Tab"]), 'S/.', Paragraph('{:,.2f}'.format(self.bonus or 0.00), styles["Right"])],
			[Paragraph('-  Prom Comisión', styles["Tab"]), 'S/.', Paragraph('{:,.2f}'.format(self.commission or 0.00), styles["Right"])],
		]

		datat += [[Paragraph('TOTAL', styles["RightBold"]), 'S/.', Paragraph('{:,.2f}'.format(self.computable_remuneration or 0.00), styles["RightBold"])],
				  [Paragraph('<u>CALCULO</u>', styles["LeftBold"]), '', ''],
				  [Paragraph('  -  Por los meses completos:', styles["LeftBold"]), '', ''],
				  [Paragraph("S/. %s ÷ 12 x %d mes(es)" % ('{:,.2f}'.format(self.computable_remuneration or 0.00), self.months or 0), styles["Tab"]),
				   'S/.', Paragraph('{:,.2f}'.format(self.cts_per_month or 0.00), styles["Right"])],
				  [Paragraph('  -  Por los dias completos:', styles["LeftBold"]), '', ''],
				  [Paragraph("S/. %s ÷ 12 ÷ 30 x %d día(s)" % ('{:,.2f}'.format(self.computable_remuneration or 0.00), self.days or 0), styles["Tab"]),
				   'S/.', Paragraph('{:,.2f}'.format(self.cts_per_day or 0.00), styles["Right"])],
				  [Paragraph('  -  Faltas:', styles["LeftBold"]), '', ''],
				  [Paragraph("S/. %s ÷ 12 ÷ 30 x %d día(s)" % ('{:,.2f}'.format(self.computable_remuneration or 0.00), self.lacks or 0), styles["Tab"]),
				   'S/. ', Paragraph('{:,.2f}'.format(-self.amount_per_lack or 0.00), styles["Right"])],
				  [Paragraph('  -  Interes CTS:', styles["LeftBold"]), 'S/. ', Paragraph('{:,.2f}'.format(self.cts_interest or 0.00), styles["Right"])],
				  [Paragraph('  -  Otros Descuentos:', styles["LeftBold"]), 'S/. ', Paragraph('{:,.2f}'.format(-self.other_discounts or 0.00), styles["Right"])],
				  [Paragraph('TOTAL', styles["RightBold"]), 'S/.', Paragraph('{:,.2f}'.format(self.total_cts or 0.00), styles["RightBold"])],
				  ['', '', ''], ]

		table2 = Table(datat, colWidths=[350, 20, 80])
		table2.setStyle(TableStyle(
			[
				('FONTSIZE', (0, 0), (-1, -1), 10),
				('FONT', (0, 0), (-1, -1), 'Times-Bold'),
				('ALIGN', (0, 2), (-1, 2), 'RIGHT'),
				('LINEABOVE', (2, 11),
				 (2, 11), 1.3, colors.black),
				('LINEABOVE', (2, 21),
				 (2, 21), 1.3, colors.black),
			]
		))
		elements.append(Spacer(0, 1))
		elements.append(table2)

		if cts_account.currency_id.name == 'USD':
			datat = [
				[Paragraph('MONTO DEPOSITADO (*)', styles["LeftBold"]), '$', Paragraph(str(self.cts_dollars), styles["RightBold"])],
				['', '', ''],
				[Paragraph("(*) Moneda Extranjera: Tipo de Cambio {0}".format(self.exchange_type), styles["LeftBold"]), '', ''],
				['', '', ''],
			]
			table3 = Table(datat, colWidths=[350, 20, 80])
			table3.setStyle(TableStyle(
				[
					('FONTSIZE', (0, 0), (-1, -1), 10),
					('FONT', (0, 0), (-1, -1), 'Times-Bold'),
					('BOX', (2, 0), (2, 0), 1.3, colors.black),
				]
			))
			elements.append(table3)
		elements.append(Spacer(0, 30))

		I = ReportBase.create_image(MainParameter.signature, MainParameter.dir_create_file + 'signature.jpg', 160.0, 35.0)
		dataf = [
			[I if I else '','',''],
			[MainParameter.reprentante_legal_id.name or '', '', self.employee_id.name or ''],
			["%s: %s" % (MainParameter.reprentante_legal_id.l10n_latam_identification_type_id.name or '',
						 MainParameter.reprentante_legal_id.vat or ''), '',
			 "%s: %s" % (self.employee_id.type_document_id.name or '', self.employee_id.identification_id or '')],
			['Empleador', '', 'Trabajador(a)'],
		]
		table4 = Table(dataf, colWidths=[200, 50, 200])
		table4.setStyle(TableStyle(
			[
				('FONTSIZE', (0, 0), (-1, -1), 10),
				('FONT', (0, 0), (-1, -1), 'Times-Bold'),
				('ALIGN', (0, 0), (-1, -1), 'CENTER'),
				('LINEABOVE', (0, 1), (0, 1), 1.1, colors.black),
				('LINEABOVE', (2, 1), (2, 1), 1.1, colors.black),
			]
		))
		elements.append(table4)
		elements.append(PageBreak())
		return elements

