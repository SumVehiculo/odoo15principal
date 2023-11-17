# -*- coding:utf-8 -*-
from odoo import api, fields, models

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, inch, landscape
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_RIGHT, TA_LEFT
from odoo.exceptions import UserError
from datetime import *
import base64

class HrEmployee(models.Model):
	_inherit = 'hr.employee'

	liquidation_id = fields.Many2one('hr.liquidation')

	def get_liquidation_employee(self):
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		if not MainParameter.dir_create_file:
			raise UserError(u'No existe un Directorio de Descarga configurado en Parametros Principales de Nomina para su Compañía')
		doc = SimpleDocTemplate(MainParameter.dir_create_file + 'Liquidacion de Beneficios Sociales.pdf', pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=20)
		elements = []
		for record in self:
			if record.liquidation_id:
				if MainParameter.type_liquidation== '1':
					elements += record.get_pdf_liquidation()
				elif MainParameter.type_liquidation== '2':
					elements += record.get_pdf_liquidation_v2()
		doc.build(elements)
		f = open(MainParameter.dir_create_file + 'Liquidacion de Beneficios Sociales.pdf', 'rb')
		return self.env['popup.it'].get_file('Liquidacion de Beneficios Sociales.pdf',base64.encodebytes(b''.join(f.readlines())))

	def get_pdf_liquidation(self):
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		ReportBase = self.env['report.base']
		Liquidation = self.liquidation_id
		year = int(Liquidation.fiscal_year_id.name)
		cts_period = MainParameter.get_month_name(5 if Liquidation.cts_type == '11' else 11)
		gratification_period = MainParameter.get_month_name(1 if Liquidation.gratification_type == '07' else 7)
		Gratification_Line = Liquidation.gratification_line_ids.filtered(lambda line: line.employee_id == self)
		Cts_Line = Liquidation.cts_line_ids.filtered(lambda line: line.employee_id == self)
		Vacation_Line = Liquidation.vacation_line_ids.filtered(lambda line: line.employee_id == self)
		vacation_period_start = MainParameter.get_month_name(int(Vacation_Line.compute_date.month))
		vacation_period_end = MainParameter.get_month_name(int(Vacation_Line.cessation_date.month))

		# ExtraTotal=self.env['hr.extra.concept'].search([('liquidation_id', '=', Liquidation.id),('employee_id', '=',self.id)],limit=1)
		ExtraTotal = Liquidation.liq_ext_concept_ids.filtered(lambda l: l.employee_id == self)
		# print("ExtraLine",ExtraLine)
		total_income = Cts_Line.total_cts + Vacation_Line.total_vacation + Gratification_Line.total_grat + Gratification_Line.bonus_essalud + ExtraTotal.income
		total_discount = Vacation_Line.afp_jub + Vacation_Line.afp_mixed_com + Vacation_Line.afp_fixed_com + Vacation_Line.afp_si + Vacation_Line.onp + ExtraTotal.expenses
		total = ReportBase.custom_round(total_income - total_discount, 2)

		Lot = Liquidation.payslip_run_id
		Slip = Lot.slip_ids.filtered(lambda slip: slip.employee_id == self)
		Last_Contract = Slip.contract_id

		cessation_period = MainParameter.get_month_name(int(Last_Contract.date_end.month))
		First_Contract = self.env['hr.contract'].get_first_contract(self, Last_Contract)
		days, months = MainParameter.get_months_days_difference(First_Contract.date_start, Last_Contract.date_end)
		elements = []
		style_title = ParagraphStyle(name='Center', alignment=TA_CENTER, fontSize=12, fontName="times-roman")
		style_cell = ParagraphStyle(name='Center', alignment=TA_CENTER, fontSize=8.0, fontName="times-roman")
		style_right = ParagraphStyle(name='Center', alignment=TA_RIGHT, fontSize=8.0, fontName="times-roman")
		style_left = ParagraphStyle(name='Center', alignment=TA_LEFT, fontSize=8.0, fontName="times-roman")
		style_left_tab = ParagraphStyle(name='Center', alignment=TA_LEFT, fontSize=8.0, fontName="times-roman", leftIndent=14)
		internal_width = [2.5 * cm]
		simple_style = [('ALIGN', (0, 0), (-1, -1), 'CENTER'),
						('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]
		bg_color = colors.HexColor("#c5d9f1")
		spacer = Spacer(5, 20)

		global_format = [
			('ALIGN', (0, 0), (-1, -1), 'CENTER'),
			('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
		]

		I = ReportBase.create_image(self.env.company.logo, MainParameter.dir_create_file + 'logo.jpg', 140.0, 35.0)
		data = [[I if I else '', Paragraph('<strong>LIQUIDACION BENEFICIOS SOCIALES</strong> <br/>\
											  LIQUIDACION BENEFICIOS SOCIALES QUE OTORGA <br/>\
											  %s' % self.env.company.name, style_cell),'']]
		t = Table(data, [5 * cm, 12 * cm, 3 * cm])
		t.setStyle(TableStyle([('ALIGN', (0, 0), (0, 0), 'LEFT'),
							   ('ALIGN', (1, 0), (1, 0), 'CENTER'),
							   ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]))
		elements.append(t)
		elements.append(Spacer(5, 10))

		data = [
				[Paragraph('<strong>DATOS PERSONALES</strong>', style_left)],
				[Paragraph('<strong>Apellidos y Nombres</strong>', style_left_tab), ':', Paragraph(self.name or '', style_left)],
				[Paragraph(u'<strong>DNI N°</strong>', style_left_tab), ':', Paragraph(self.identification_id or '', style_left)],
				[Paragraph('<strong>Cargo</strong>', style_left_tab), ':', Paragraph(self.job_id.name or '', style_left)],
				[Paragraph('<strong>Fecha Ingreso</strong>', style_left_tab), ':', Paragraph(str(First_Contract.date_start) or '', style_left)],
				[Paragraph('<strong>Fecha Cese</strong>', style_left_tab), ':', Paragraph(str(Last_Contract.date_end) or '', style_left)],
				[Paragraph('<strong>Motivo</strong>', style_left_tab), ':', Paragraph(Last_Contract.situation_reason_id.name.title() or '', style_left)],
				[Paragraph(u'<strong>Afiliación</strong>', style_left_tab), ':', Paragraph(Last_Contract.membership_id.name or '', style_left)],
				[Paragraph(u'<strong>Ultimo Sueldo Básico</strong>', style_left_tab), ':', Paragraph('%d NUEVOS SOLES' % Last_Contract.wage, style_left),
				 Paragraph('<strong>Tipo de Cambio</strong> %d' % Liquidation.exchange_type, style_left)],
				[Paragraph(u'<strong>Tiempo de Servicios</strong>', style_left_tab), ':', Paragraph('%d MES(ES) y %d DIA(S)' % (months, days), style_left)],
				[''],
				[Paragraph('<strong>BASES DE CALCULO</strong>', style_left)],
				[Paragraph('<strong>1. COMPENSACION POR TIEMPO DE SERVICIOS</strong>', style_left)],
				[Paragraph('<strong>(Periodo {start} {start_year} a {end} {end_year})</strong>'.format(start=cts_period,
																								 start_year= year if Liquidation.cts_type == '11' else str(int(year) - 1),
																								 end=cessation_period,
																								 end_year=year), style_left)],
				[Paragraph('<strong>CTS Trunca</strong>', style_left_tab), ':', Paragraph('{:,.2f}'.format(Cts_Line.total_cts) or '0.00', style_left)],
				[Paragraph('<strong>Tiempo</strong>', style_left_tab), ':', Paragraph('%d mes(es) y %d dia(s)' % (Cts_Line.months or 0,Cts_Line.days or 0), style_left)],
				[''],
				[Paragraph('<strong>2. VACACIONES</strong>', style_left)],
				[Paragraph('<strong>(Periodo {start} {start_year} a {end} {end_year})</strong>'.format(start=vacation_period_start,
																									   start_year=Vacation_Line.admission_date.year,
																									   end=vacation_period_end,
																									   end_year=Vacation_Line.cessation_date.year), style_left)],
				[Paragraph('<strong>Vacaciones Truncas</strong>', style_left_tab), ':', Paragraph('{:,.2f}'.format(Vacation_Line.truncated_vacation) or '0.00', style_left)],
				[Paragraph('<strong>Adelanto de Vacaciones</strong>', style_left_tab), ':', Paragraph('- {:,.2f}'.format(Vacation_Line.advanced_vacation) or '0.00', style_left)],
				[Paragraph('<strong>Tiempo</strong>', style_left_tab), ':', Paragraph('%d mes(es) y %d dia(s)' % (Vacation_Line.months or 0,Vacation_Line.days or 0), style_left)],
				[''],
				[Paragraph('<strong>3. GRATIFICACIONES</strong>', style_left)],
				[Paragraph('<strong>(Periodo {start} {year} a {end} {year})</strong>'.format(start=gratification_period,
																							 end=cessation_period,
																							 year=year), style_left)],
				[Paragraph(u'<strong>Gratificación Trunca</strong>', style_left_tab), ':', Paragraph('{:,.2f}'.format(Gratification_Line.total_grat) or '0.00', style_left)],
				[Paragraph('<strong>Bono Ex. L. 30334</strong>', style_left_tab), ':', Paragraph('{:,.2f}'.format(Gratification_Line.bonus_essalud) or '0.00', style_left)],
				[Paragraph('<strong>Tiempo</strong>', style_left_tab), ':', Paragraph('%d mes(es) y %d dia(s)' % (Gratification_Line.months or 0, Gratification_Line.days or 0,), style_left)],
				[''],
				[Paragraph('<strong>4. LIQUIDACION</strong>', style_left)],
				[Paragraph('<strong>(Periodo {start} {start_year} a {end} {end_year})</strong>'.format(start=vacation_period_start,
																								start_year=Vacation_Line.admission_date.year,
																							 	end=cessation_period,
																							 	end_year=year), style_left)],
				[Paragraph('<strong>CTS Trunca</strong>', style_left_tab), ':', Paragraph('{:,.2f}'.format(Cts_Line.total_cts) or '0.00', style_left)],
				[Paragraph('<strong>Vacaciones Truncas</strong>', style_left_tab), ':', Paragraph('{:,.2f}'.format(Vacation_Line.total_vacation) or '0.00', style_left)],
				[Paragraph(u'<strong>Gratificación Trunca</strong>', style_left_tab), ':', Paragraph('{:,.2f}'.format(Gratification_Line.total_grat) or '0.00', style_left)],
				[Paragraph('<strong>Bono Ex. L. 30334</strong>', style_left_tab), ':', Paragraph('{:,.2f}'.format(Gratification_Line.bonus_essalud) or '0.00', style_left)],
				[''],
				[Paragraph('<strong>OTROS INGRESOS</strong>', style_left)],
			]
		ExtraLine=self.env['hr.extra.concept'].search([('liquidation_id', '=', Liquidation.id),('employee_id', '=',self.id)],limit=1)
		In_Concepts = ExtraLine.conceptos_lines.filtered(lambda c: c.type == 'in')
		Out_Concepts = ExtraLine.conceptos_lines.filtered(lambda c: c.type == 'out')
		in_data, out_data = [], []
		for inc in In_Concepts:
			in_data.append([Paragraph('<strong>{0}</strong>'.format(inc.name_input_id.name.title()), style_left_tab), ':', Paragraph('{:,.2f}'.format(inc.amount) or '0.00', style_left)])
		data += in_data
		data += [
				[''],
				[Paragraph('<strong>TOTAL INGRESOS</strong>', style_left_tab), '', Paragraph('{:,.2f}'.format(total_income) or '0.00', style_right)],
				[''],
				[Paragraph('<strong>OTROS DESCUENTOS</strong>', style_left)],
				[Paragraph('<strong>Aportes Trabajador</strong>', style_left)],
				[Paragraph('<strong>AFP Fondo de Pensiones</strong>', style_left_tab), ':', Paragraph('{:,.2f}'.format(Vacation_Line.afp_jub) or '0.00', style_left)],
				[Paragraph('<strong>AFP Comision Porc.</strong>', style_left_tab), ':', Paragraph('{:,.2f}'.format(Vacation_Line.afp_mixed_com + Vacation_Line.afp_fixed_com) or '0.00', style_left)],
				[Paragraph('<strong>AFP Prima de Seguros</strong>', style_left_tab), ':', Paragraph('{:,.2f}'.format(Vacation_Line.afp_si) or '0.00', style_left)],
				[Paragraph('<strong>Fondo ONP</strong>', style_left_tab), ':', Paragraph('{:,.2f}'.format(Vacation_Line.onp) or '0.00', style_left)],
				[''],
			]
		for ouc in Out_Concepts:
			out_data.append([Paragraph('<strong>{0}</strong>'.format(ouc.name_input_id.name.title()), style_left_tab), ':', Paragraph('{:,.2f}'.format(ouc.amount) or '0.00', style_left)])
		data += out_data
		data += [
				[''],
				[Paragraph('<strong>TOTAL DESCUENTOS</strong>', style_left_tab), '', Paragraph('{:,.2f}'.format(total_discount) or '0.00', style_right)],
				[Paragraph('<strong>TOTAL A PAGAR</strong>', style_left_tab), '', Paragraph('{:,.2f}'.format(total) or '0.00', style_right)],
		]
		t = Table(data, [8 * cm, 1 * cm, 7 * cm, 4 * cm], len(data) * [0.32 * cm])
		t.setStyle(TableStyle(global_format))
		elements.append(t)

		I = ReportBase.create_image(MainParameter.signature, MainParameter.dir_create_file + 'signature.jpg', 140.0, 40.0)
		data = [
			[Paragraph('<strong>Neto a Pagar al Trabajador</strong>', style_left)],
			[Paragraph(
				'<strong>son: {0} soles</strong>'.format(MainParameter.number_to_letter(total_income - total_discount)),
				style_left_tab)],
			[I if I else '', '', '', Paragraph('{0} {1} de {2} del {3}'.format(self.env.company.city or '',
																			   Last_Contract.date_end.day,
																			   MainParameter.get_month_name(
																				   Last_Contract.date_end.month),
																			   Last_Contract.date_end.year),
											   style_cell)],
			[Paragraph(
				'<strong>__________________________________________<br/>%s<br/>%s N° %s</strong>' % (MainParameter.reprentante_legal_id.name or '',
																							  MainParameter.reprentante_legal_id.l10n_latam_identification_type_id.name or '',
																							  MainParameter.reprentante_legal_id.vat or ''),
				style_cell)],
			# [''],
			[Paragraph('<strong><br/>CONSTANCIA DE RECEPCION</strong>', style_left)],
			[Paragraph('Declaro estar conforme con la presente liquidación, haber recibido el importe de la misma \
									así como el importe correspondiente a todas y cada una de mis remuneraciones y beneficios no \
									teniendo que reclamar en el futuro, quedando asi concluida la relación laboral.',
					   style_cell)],
			[''],
			[Paragraph('<strong>____________________________________<br/>%s<br/>%s N° %s</strong>' % (
				self.name or '', self.type_document_id.name or '', self.identification_id or ''), style_cell)],
		]
		t = Table(data, [8 * cm, 1 * cm, 5 * cm, 6 * cm], len(data) * [0.9 * cm])
		t.setStyle(TableStyle([
			('ALIGN', (0, 0), (-1, -1), 'CENTER'),
			('SPAN', (0, 1), (1, 1)),
			('SPAN', (0, 5), (-1, 5)),
			('SPAN', (0, 7), (-1, 7)),
			('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
		]))
		elements.append(t)
		elements.append(PageBreak())

		return elements


	def get_pdf_liquidation_v2(self):
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		ReportBase = self.env['report.base']
		Liquidation = self.liquidation_id
		year = int(Liquidation.fiscal_year_id.name)
		cts_period = MainParameter.get_month_name(5 if Liquidation.cts_type == '11' else 11)
		gratification_period = MainParameter.get_month_name(1 if Liquidation.gratification_type == '07' else 7)
		# print("cts_period",cts_period)
		# print("gratification_period",gratification_period)
		Gratification_Line = Liquidation.gratification_line_ids.filtered(lambda line: line.employee_id == self)
		Cts_Line = Liquidation.cts_line_ids.filtered(lambda line: line.employee_id == self)
		Vacation_Line = Liquidation.vacation_line_ids.filtered(lambda line: line.employee_id == self)
		vacation_period_start = MainParameter.get_month_name(int(Vacation_Line.compute_date.month))
		vacation_period_end = MainParameter.get_month_name(int(Vacation_Line.cessation_date.month))

		ExtraTotal = Liquidation.liq_ext_concept_ids.filtered(lambda l: l.employee_id == self)
		total_income = Cts_Line.total_cts + Vacation_Line.total_vacation + Gratification_Line.total_grat + Gratification_Line.bonus_essalud + ExtraTotal.income
		total_discount = Vacation_Line.afp_jub + Vacation_Line.afp_mixed_com + Vacation_Line.afp_fixed_com + Vacation_Line.afp_si + Vacation_Line.onp + ExtraTotal.expenses
		total = ReportBase.custom_round(total_income - total_discount, 2)

		Lot = Liquidation.payslip_run_id
		Slip = Lot.slip_ids.filtered(lambda slip: slip.employee_id == self)
		Last_Contract = Slip.contract_id

		cessation_period = MainParameter.get_month_name(int(Last_Contract.date_end.month))
		First_Contract = self.env['hr.contract'].get_first_contract(self, Last_Contract)
		days, months = MainParameter.get_months_days_difference(First_Contract.date_start, Last_Contract.date_end)

		elements = []
		style_title = ParagraphStyle(name='Center', alignment=TA_CENTER, fontSize=12, fontName="times-roman")
		style_cell = ParagraphStyle(name='Center', alignment=TA_CENTER, fontSize=7.0, fontName="times-roman")
		style_right = ParagraphStyle(name='Center', alignment=TA_RIGHT, fontSize=8.5, fontName="times-roman")
		style_left = ParagraphStyle(name='Center', alignment=TA_LEFT, fontSize=8.5, fontName="times-roman")
		style_left_tab = ParagraphStyle(name='Center', alignment=TA_LEFT, fontSize=8.0, fontName="times-roman", leftIndent=16)
		style_left_tab_seg = ParagraphStyle(name='Center', alignment=TA_LEFT, fontSize=8.0, fontName="times-roman", leftIndent=32)
		style_left_tab_ter = ParagraphStyle(name='Center', alignment=TA_LEFT, fontSize=8.0, fontName="times-roman", leftIndent=38)
		style_center = ParagraphStyle(name='Center', alignment=TA_CENTER, fontSize=10, fontName="times-roman")
		internal_width = [2.5 * cm]
		simple_style = [('ALIGN', (0, 0), (-1, -1), 'CENTER'),
						('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]
		bg_color = colors.HexColor("#c5d9f1")
		spacer = Spacer(2, 15)

		global_format = [
			('ALIGN', (0, 0), (-1, -1), 'CENTER'),
			('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
		]

		I = ReportBase.create_image(self.env.company.logo, MainParameter.dir_create_file + 'logo.jpg', 110.0, 70.0)
		data = [
			[I if I else '','',
			Paragraph('<strong>Empresa</strong>', style_left), Paragraph(self.env.company.name or '', style_left)],
			['','',Paragraph(u'<strong>R.U.C.</strong>', style_left), Paragraph(str(self.env.company.vat) or '', style_left)]
			]
		t = Table(data, [4 * cm, 7 * cm,2 * cm, 7 * cm],len(data) * [0.52 * cm])
		t.setStyle(TableStyle([
            ('SPAN', (0, 0), (0, -1)),
            ('ALIGN', (0, 0), (0, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
            ]))
		elements.append(t)
		elements.append(Spacer(2, 6))

		data = [
			[Paragraph('<strong>LIQUIDACION DE BENEFICIOS SOCIALES</strong>', style_title)]
		]
		t = Table(data, [20 * cm])
		t.setStyle(TableStyle(global_format))
		elements.append(t)

		data = [
				[Paragraph('Apellidos y Nombres', style_left),Paragraph(': %s' % self.name or '', style_left),
				 Paragraph('Centro de Costos', style_left),Paragraph(': %s' % Last_Contract.distribution_id.name or '', style_left)],
				[Paragraph('DNI', style_left),Paragraph(': %s' % str(self.identification_id) or '', style_left),
				 Paragraph('Area de Trabajo', style_left),Paragraph(': %s' % self.department_id.name or '', style_left)],
				[Paragraph('Fecha de Ingreso', style_left),Paragraph(': %s' % str(First_Contract.date_start) or '', style_left),
				 Paragraph('Cargo', style_left),Paragraph(': %s' % self.job_id.name or '', style_left)],
				[Paragraph('Fecha de Salida', style_left),Paragraph(': %s' % str(Last_Contract.date_end) or '', style_left),
				 Paragraph('Tiempo de Servicio', style_left),Paragraph(': %d Año(s) %d Mes(es) y %d Dia(s)' % (months/12 if months>12 else 0,months if months<=12 else months%12, days) or '', style_left)],
				[Paragraph('Basico', style_left),Paragraph(': S/ {:,.2f}'.format(Last_Contract.wage or 0.00), style_left),
				 Paragraph('Periodo Liquidar', style_left),Paragraph(': %s' % Liquidation.payslip_run_id.name.name or '', style_left)],
				[Paragraph('Motivo de Cese', style_left),Paragraph(': %s' % Last_Contract.situation_reason_id.name.title() or '', style_left),
				 Paragraph('CTS', style_left),Paragraph('=> Años: 0 Meses: %d Dias: %d' % (Cts_Line.months or 0,Cts_Line.days or 0) or '', style_left)],
				[Paragraph('Regimen Laboral', style_left),Paragraph(': %s' % dict(Last_Contract._fields['labor_regime'].selection).get(Last_Contract.labor_regime) or '', style_left),
				 Paragraph('VACACIONES', style_left),Paragraph('=> Años: %d Meses: %d Dias: %d' % (Vacation_Line.months/12 if Vacation_Line.months>12 else 0,Vacation_Line.months if Vacation_Line.months<=12 else Vacation_Line.months%12,Vacation_Line.days or 0) or '', style_left)],
				[Paragraph(u'Afiliación', style_left),Paragraph(': %s' % Last_Contract.membership_id.name or '', style_left),
				 Paragraph('GRATIFICACION', style_left),Paragraph('=> Años: 0 Meses: %d Dias: %d' % (Gratification_Line.months or 0, Gratification_Line.days or 0) or '', style_left)]
		]
		t = Table(data, [3 * cm, 8 * cm , 3 * cm, 6 * cm], len(data) * [0.42 * cm])
		t.setStyle(TableStyle(global_format))
		elements.append(t)

		data = [
			[Paragraph('<strong>_______________________________________________________________________________________________________________________________</strong>', style_left)]
		]
		t = Table(data, [20 * cm],len(data) * [0.12 * cm])
		t.setStyle(TableStyle(global_format))
		elements.append(t)
		elements.append(spacer)

		data = [
			[Paragraph('<strong>1) COMPENSACION POR TIEMPO DE SERVICIOS</strong>', style_left_tab)],
			[Paragraph('<strong>- Base Imponible de C.T.S</strong>', style_left_tab_seg)],
			[Paragraph('Basico', style_left_tab_ter), Paragraph('{:,.2f}'.format(Cts_Line.wage or 0.00), style_right),'']
		]

		t = Table(data, [8 * cm, 3 * cm, 9 * cm], len(data) * [0.42 * cm])
		t.setStyle(TableStyle(global_format))
		elements.append(t)

		if Cts_Line.household_allowance != 0:
			data = [
				[Paragraph('Asignacion Familiar', style_left_tab_ter), Paragraph('{:,.2f}'.format(Cts_Line.household_allowance or 0.00), style_right),'']
			]
			t = Table(data, [8 * cm, 3 * cm, 9 * cm], len(data) * [0.42 * cm])
			t.setStyle(TableStyle(global_format))
			elements.append(t)

		if Cts_Line.sixth_of_gratification != 0:
			data = [
				[Paragraph('1/6 de Gratificacion', style_left_tab_ter), Paragraph('{:,.2f}'.format(Cts_Line.sixth_of_gratification or 0.00), style_right),'']
			]
			t = Table(data, [8 * cm, 3 * cm, 9 * cm], len(data) * [0.42 * cm])
			t.setStyle(TableStyle(global_format))
			elements.append(t)

		if Cts_Line.commission != 0:
			data = [
				[Paragraph('Prom. Comisiones', style_left_tab_ter), Paragraph('{:,.2f}'.format(Cts_Line.commission or 0.00), style_right),'']
			]
			t = Table(data, [8 * cm, 3 * cm, 9 * cm], len(data) * [0.42 * cm])
			t.setStyle(TableStyle(global_format))
			elements.append(t)

		if Cts_Line.bonus != 0:
			data = [
				[Paragraph('Prom. Bonificacion', style_left_tab_ter), Paragraph('{:,.2f}'.format(Cts_Line.bonus or 0.00), style_right),'']
			]
			t = Table(data, [8 * cm, 3 * cm, 9 * cm], len(data) * [0.42 * cm])
			t.setStyle(TableStyle(global_format))
			elements.append(t)

		if Cts_Line.extra_hours != 0:
			data = [
				[Paragraph('Prom. Horas Extras', style_left_tab_ter), Paragraph('{:,.2f}'.format(Cts_Line.extra_hours or 0.00), style_right),'']
			]
			t = Table(data, [8 * cm, 3 * cm, 9 * cm], len(data) * [0.42 * cm])
			t.setStyle(TableStyle(global_format))
			elements.append(t)

		data = [
			['',Paragraph('_______________<br/>%s' % ('{:,.2f}'.format(Cts_Line.computable_remuneration or 0.00)), style_right),'']
		]
		t = Table(data, [8 * cm, 3 * cm, 9 * cm], len(data) * [0.42 * cm])
		t.setStyle(TableStyle(global_format))
		elements.append(t)

		if Last_Contract.labor_regime == 'general':
			data = [
				[Paragraph('<strong>- C.T.S. por Depositar</strong>', style_left_tab_seg),'','','',''],
			]
			t = Table(data, [8 * cm, 4 * cm, 2 * cm, 3 * cm,3 * cm], len(data) * [0.42 * cm])
			t.setStyle(TableStyle(global_format))
			elements.append(t)

			if Cts_Line.months != 0:
				data = [
					[Paragraph('Por los %d mes(es)' % (Cts_Line.months or 0), style_left_tab_ter),
					 Paragraph('%s / 12 * %d' % ('{:,.2f}'.format(Cts_Line.computable_remuneration or 0.00), Cts_Line.months or 0), style_left),'=',
					 Paragraph('{:,.2f}'.format(Cts_Line.cts_per_month or 0.00), style_right), '']
				]
				t = Table(data, [8 * cm, 4 * cm, 2 * cm, 3 * cm,3 * cm], len(data) * [0.42 * cm])
				t.setStyle(TableStyle(global_format))
				elements.append(t)

			if Cts_Line.days != 0:
				data = [
					[Paragraph('Por los %d dia(s)' % (Cts_Line.days or 0), style_left_tab_ter),
					 Paragraph('%s / 12 / 30 * %d' % ('{:,.2f}'.format(Cts_Line.computable_remuneration or 0.00), Cts_Line.days or 0), style_left), '=',
					 Paragraph('{:,.2f}'.format(Cts_Line.cts_per_day or 0.00), style_right), '']
				]
				t = Table(data, [8 * cm, 4 * cm, 2 * cm, 3 * cm,3 * cm], len(data) * [0.42 * cm])
				t.setStyle(TableStyle(global_format))
				elements.append(t)

			if Cts_Line.lacks != 0:
				data = [
					[Paragraph('Dsct por %d dia(s) de Falta' % (Cts_Line.lacks or 0), style_left_tab_ter),
					 Paragraph('%s / 12 / 30 * %d' % ('{:,.2f}'.format(Cts_Line.computable_remuneration or 0.00), Cts_Line.lacks or 0), style_left), '=',
					 Paragraph('-{:,.2f}'.format(Cts_Line.amount_per_lack or 0.00), style_right), '']
				]
				t = Table(data, [8 * cm, 4 * cm, 2 * cm, 3 * cm,3 * cm], len(data) * [0.42 * cm])
				t.setStyle(TableStyle(global_format))
				elements.append(t)

			if Cts_Line.cts_interest != 0:
				data = [
					[Paragraph('Intereses', style_left_tab_ter),
					 '', '=',
					 Paragraph('{:,.2f}'.format(Cts_Line.cts_interest or 0.00), style_right), '']
				]
				t = Table(data, [8 * cm, 4 * cm, 2 * cm, 3 * cm,3 * cm], len(data) * [0.42 * cm])
				t.setStyle(TableStyle(global_format))
				elements.append(t)

			if Cts_Line.other_discounts != 0:
				data = [
					[Paragraph('Otros Descuentos', style_left_tab_ter),
					 '', '=',
					 Paragraph('{:,.2f}'.format(Cts_Line.other_discounts or 0.00), style_right), '']
				]
				t = Table(data, [8 * cm, 4 * cm, 2 * cm, 3 * cm,3 * cm], len(data) * [0.42 * cm])
				t.setStyle(TableStyle(global_format))
				elements.append(t)

			data = [
				['',
				 Paragraph('<strong>Total C.T.S. a Recibir</strong>', style_left),'= s/',
				 Paragraph('_______________<br/>{:,.2f}'.format(Cts_Line.total_cts or 0.00), style_right),'']
			]

			t = Table(data, [8 * cm, 4 * cm, 2 * cm, 3 * cm,3 * cm], len(data) * [0.42 * cm])
			t.setStyle(TableStyle(global_format))
			elements.append(t)
			# elements.append(spacer)
		else:
			data = [
				[Paragraph('<strong>- C.T.S. por Depositar</strong>', style_left_tab_seg),'','','',''],
			]
			t = Table(data, [8 * cm, 4 * cm, 2 * cm, 3 * cm,3 * cm], len(data) * [0.42 * cm])
			t.setStyle(TableStyle(global_format))
			elements.append(t)

			if Cts_Line.months != 0:
				data = [
					[Paragraph('Por los %d mes(es)' % (Cts_Line.months or 0), style_left_tab_ter),
					 Paragraph('%s / 2 / 12 * %d' % ('{:,.2f}'.format(Cts_Line.computable_remuneration or 0.00), Cts_Line.months or 0), style_left),'=',
					 Paragraph('{:,.2f}'.format(Cts_Line.cts_per_month or 0.00), style_right), '']
				]
				t = Table(data, [8 * cm, 4 * cm, 2 * cm, 3 * cm,3 * cm], len(data) * [0.42 * cm])
				t.setStyle(TableStyle(global_format))
				elements.append(t)

			if Cts_Line.days != 0:
				data = [
					[Paragraph('Por los %d dia(s)' % (Cts_Line.days or 0), style_left_tab_ter),
					 Paragraph('%s / 2 / 12 / 30 * %d' % ('{:,.2f}'.format(Cts_Line.computable_remuneration or 0.00), Cts_Line.days or 0), style_left),'=',
					 Paragraph('{:,.2f}'.format(Cts_Line.cts_per_day or 0.00), style_right), '']
				]
				t = Table(data, [8 * cm, 4 * cm, 2 * cm, 3 * cm,3 * cm], len(data) * [0.42 * cm])
				t.setStyle(TableStyle(global_format))
				elements.append(t)

			if Cts_Line.lacks != 0:
				data = [
					[Paragraph('Dsct por %d dia(s) de Falta' % (Cts_Line.lacks or 0), style_left_tab_ter),
					 Paragraph('%s / 2/ 12 / 30 * %d' % ('{:,.2f}'.format(Cts_Line.computable_remuneration or 0.00), Cts_Line.lacks or 0), style_left), '=',
					 Paragraph('-{:,.2f}'.format(Cts_Line.amount_per_lack or 0.00), style_right), '']
				]
				t = Table(data, [8 * cm, 4 * cm, 2 * cm, 3 * cm,3 * cm], len(data) * [0.42 * cm])
				t.setStyle(TableStyle(global_format))
				elements.append(t)

			if Cts_Line.cts_interest != 0:
				data = [
					[Paragraph('Intereses', style_left_tab_ter),
					 '', '=',
					 Paragraph('{:,.2f}'.format(Cts_Line.cts_interest or 0.00), style_right), '']
				]
				t = Table(data, [8 * cm, 4 * cm, 2 * cm, 3 * cm,3 * cm], len(data) * [0.42 * cm])
				t.setStyle(TableStyle(global_format))
				elements.append(t)

			if Cts_Line.other_discounts != 0:
				data = [
					[Paragraph('Otros Descuentos', style_left_tab_ter),
					 '', '=',
					 Paragraph('{:,.2f}'.format(Cts_Line.other_discounts or 0.00), style_right), '']
				]
				t = Table(data, [8 * cm, 4 * cm, 2 * cm, 3 * cm,3 * cm], len(data) * [0.42 * cm])
				t.setStyle(TableStyle(global_format))
				elements.append(t)

			data = [
				['',
				 Paragraph('<strong>Total C.T.S. a Recibir</strong>', style_left),'= s/',
				 Paragraph('_______________<br/>{:,.2f}'.format(Cts_Line.total_cts or 0.00), style_right),'']
			]

			t = Table(data, [8 * cm, 4 * cm, 2 * cm, 3 * cm,3 * cm], len(data) * [0.42 * cm])
			t.setStyle(TableStyle(global_format))
			elements.append(t)

		# elements.append(spacer)

		data = [
			[Paragraph('<strong>2) GRATIFICACIONES DEL TRABAJADOR</strong>', style_left_tab)],
			[Paragraph('<strong>- Base Imponible de Gratificacion</strong>', style_left_tab_seg)],
			[Paragraph('Basico', style_left_tab_ter), Paragraph('{:,.2f}'.format(Gratification_Line.wage or 0.00), style_right),'']
		]

		t = Table(data, [8 * cm, 3 * cm, 9 * cm], len(data) * [0.42 * cm])
		t.setStyle(TableStyle(global_format))
		elements.append(t)

		if Gratification_Line.household_allowance != 0:
			data = [
				[Paragraph('Asignacion Familiar', style_left_tab_ter), Paragraph('{:,.2f}'.format(Gratification_Line.household_allowance or 0.00), style_right),'']
			]
			t = Table(data, [8 * cm, 3 * cm, 9 * cm], len(data) * [0.42 * cm])
			t.setStyle(TableStyle(global_format))
			elements.append(t)

		if Gratification_Line.commission != 0:
			data = [
				[Paragraph('Prom. Comisiones', style_left_tab_ter), Paragraph('{:,.2f}'.format(Gratification_Line.commission or 0.00), style_right),'']
			]
			t = Table(data, [8 * cm, 3 * cm, 9 * cm], len(data) * [0.42 * cm])
			t.setStyle(TableStyle(global_format))
			elements.append(t)

		if Gratification_Line.bonus != 0:
			data = [
				[Paragraph('Prom. Bonificacion', style_left_tab_ter), Paragraph('{:,.2f}'.format(Gratification_Line.bonus or 0.00), style_right),'']
			]
			t = Table(data, [8 * cm, 3 * cm, 9 * cm], len(data) * [0.42 * cm])
			t.setStyle(TableStyle(global_format))
			elements.append(t)

		if Gratification_Line.extra_hours != 0:
			data = [
				[Paragraph('Prom. Horas Extras', style_left_tab_ter), Paragraph('{:,.2f}'.format(Gratification_Line.extra_hours or 0.00), style_right),'']
			]
			t = Table(data, [8 * cm, 3 * cm, 9 * cm], len(data) * [0.42 * cm])
			t.setStyle(TableStyle(global_format))
			elements.append(t)

		data = [
			['',Paragraph('_______________<br/>%s' % ('{:,.2f}'.format(Gratification_Line.computable_remuneration or 0.00)), style_right),'']
		]
		t = Table(data, [8 * cm, 3 * cm, 9 * cm], len(data) * [0.42 * cm])
		t.setStyle(TableStyle(global_format))
		elements.append(t)

		if Last_Contract.labor_regime == 'general':
			data = [
				[Paragraph('<strong>- Gratificaciones por Percibir</strong>', style_left_tab_seg),'','','',''],
			]
			t = Table(data, [8 * cm, 4 * cm, 2 * cm, 3 * cm,3 * cm], len(data) * [0.42 * cm])
			t.setStyle(TableStyle(global_format))
			elements.append(t)

			if Gratification_Line.months != 0:
				data = [
					[Paragraph('Por los %d mes(es)' % (Gratification_Line.months or 0), style_left_tab_ter),
					 Paragraph('%s / 6 * %d' % ('{:,.2f}'.format(Gratification_Line.computable_remuneration or 0.00),Gratification_Line.months or 0), style_left), '=',
					 Paragraph('{:,.2f}'.format(Gratification_Line.grat_per_month or 0.00), style_right), '']
				]
				t = Table(data, [8 * cm, 4 * cm, 2 * cm, 3 * cm,3 * cm], len(data) * [0.42 * cm])
				t.setStyle(TableStyle(global_format))
				elements.append(t)

			if Gratification_Line.days != 0:
				data = [
					[Paragraph('Por los %d dia(s)' % (Gratification_Line.days or 0), style_left_tab_ter),
					 Paragraph('%s / 6 / 30 * %d' % ('{:,.2f}'.format(Gratification_Line.computable_remuneration or 0.00),Gratification_Line.days or 0), style_left), '=',
					 Paragraph('{:,.2f}'.format(Gratification_Line.grat_per_day or 0.00), style_right), '']
				]
				t = Table(data, [8 * cm, 4 * cm, 2 * cm, 3 * cm,3 * cm], len(data) * [0.42 * cm])
				t.setStyle(TableStyle(global_format))
				elements.append(t)

			if Gratification_Line.lacks != 0:
				data = [
					[Paragraph('Dsct por %d dia(s) de Falta' % (Gratification_Line.lacks or 0), style_left_tab_ter),
					 Paragraph('%s / 6 / 30 * %d' % ('{:,.2f}'.format(Gratification_Line.computable_remuneration or 0.00), Gratification_Line.lacks or 0), style_left), '=',
					 Paragraph('-{:,.2f}'.format(Gratification_Line.amount_per_lack or 0.00), style_right), '']
				]
				t = Table(data, [8 * cm, 4 * cm, 2 * cm, 3 * cm,3 * cm], len(data) * [0.42 * cm])
				t.setStyle(TableStyle(global_format))
				elements.append(t)

			if Gratification_Line.bonus_essalud != 0:
				data = [
					[Paragraph('Bonif. Extr. 30334', style_left_tab_ter),
					 Paragraph('%s * %s %s' % ('{:,.2f}'.format(Gratification_Line.total_grat or 0.00),str(Last_Contract.social_insurance_id.percent),'%'), style_left), '=',
					 Paragraph('{:,.2f}'.format(Gratification_Line.bonus_essalud or 0.00), style_right),'']
				]
				t = Table(data, [8 * cm, 4 * cm, 2 * cm, 3 * cm,3 * cm], len(data) * [0.42 * cm])
				t.setStyle(TableStyle(global_format))
				elements.append(t)

			data = [
				['',
				 Paragraph('<strong>Total Grat. a Recibir</strong>', style_left), '= s/',
				 Paragraph('_______________<br/>{:,.2f}'.format(Gratification_Line.total or 0.00), style_right), '']
			]

			t = Table(data, [8 * cm, 4 * cm, 2 * cm, 3 * cm,3 * cm], len(data) * [0.42 * cm])
			t.setStyle(TableStyle(global_format))
			elements.append(t)
			# elements.append(spacer)
		else:
			data = [
				[Paragraph('<strong>- Gratificaciones por Percibir</strong>', style_left_tab_seg),'','','',''],
			]
			t = Table(data, [8 * cm, 4 * cm, 2 * cm, 3 * cm,3 * cm], len(data) * [0.42 * cm])
			t.setStyle(TableStyle(global_format))
			elements.append(t)

			if Gratification_Line.months != 0:
				data = [
					[Paragraph('Por los %d mes(es)' % (Gratification_Line.months or 0), style_left_tab_ter),
					 Paragraph('%s / 2 / 6 * %d' % ('{:,.2f}'.format(Gratification_Line.computable_remuneration or 0.00),Gratification_Line.months or 0), style_left), '=',
					 Paragraph('{:,.2f}'.format(Gratification_Line.grat_per_month or 0.00), style_right), '']
				]
				t = Table(data, [8 * cm, 4 * cm, 2 * cm, 3 * cm,3 * cm], len(data) * [0.42 * cm])
				t.setStyle(TableStyle(global_format))
				elements.append(t)

			if Gratification_Line.days != 0:
				data = [
					[Paragraph('Por los %d dia(s)' % (Gratification_Line.days or 0), style_left_tab_ter),
					 Paragraph('%s / 2 / 6 / 30 * %d' % ('{:,.2f}'.format(Gratification_Line.computable_remuneration or 0.00),Gratification_Line.days or 0), style_left), '=',
					 Paragraph('{:,.2f}'.format(Gratification_Line.grat_per_day or 0.00), style_right), '']
				]
				t = Table(data, [8 * cm, 4 * cm, 2 * cm, 3 * cm,3 * cm], len(data) * [0.42 * cm])
				t.setStyle(TableStyle(global_format))
				elements.append(t)

			if Gratification_Line.lacks != 0:
				data = [
					[Paragraph('Dsct por %d dia(s) de Falta' % (Gratification_Line.lacks or 0), style_left_tab_ter),
					 Paragraph('%s / 2 / 6 / 30 * %d' % ('{:,.2f}'.format(Gratification_Line.computable_remuneration or 0.00), Gratification_Line.lacks or 0), style_left), '=',
					 Paragraph('-{:,.2f}'.format(Gratification_Line.amount_per_lack or 0.00), style_right), '']
				]
				t = Table(data, [8 * cm, 4 * cm, 2 * cm, 3 * cm,3 * cm], len(data) * [0.42 * cm])
				t.setStyle(TableStyle(global_format))
				elements.append(t)

			if Gratification_Line.bonus_essalud != 0:
				data = [
					[Paragraph('Bonif. Extr. 30334', style_left_tab_ter),
					 Paragraph('%s * %s %s' % ('{:,.2f}'.format(Gratification_Line.total_grat or 0.00),str(Last_Contract.social_insurance_id.percent),'%'), style_left), '=',
					 Paragraph('{:,.2f}'.format(Gratification_Line.bonus_essalud or 0.00), style_right),'']
				]
				t = Table(data, [8 * cm, 4 * cm, 2 * cm, 3 * cm,3 * cm], len(data) * [0.42 * cm])
				t.setStyle(TableStyle(global_format))
				elements.append(t)

			data = [
				['',
				 Paragraph('<strong>Total Grat. a Recibir</strong>', style_left), '= s/',
				 Paragraph('_______________<br/>{:,.2f}'.format(Gratification_Line.total or 0.00), style_right), '']
			]

			t = Table(data, [8 * cm, 4 * cm, 2 * cm, 3 * cm,3 * cm], len(data) * [0.42 * cm])
			t.setStyle(TableStyle(global_format))
			elements.append(t)
			# elements.append(spacer)

		data = [
			[Paragraph('<strong>3) VACACIONES DEL TRABAJADOR</strong>', style_left_tab)],
			[Paragraph('<strong>- Base Imponible de Vacaciones</strong>', style_left_tab_seg)],
			[Paragraph('Basico', style_left_tab_ter), Paragraph('{:,.2f}'.format(Vacation_Line.wage or 0.00), style_right),'']
		]

		t = Table(data, [8 * cm, 3 * cm, 9 * cm], len(data) * [0.42 * cm])
		t.setStyle(TableStyle(global_format))
		elements.append(t)

		if Vacation_Line.household_allowance != 0:
			data = [
				[Paragraph('Asignacion Familiar', style_left_tab_ter), Paragraph('{:,.2f}'.format(Vacation_Line.household_allowance or 0.00), style_right),'']
			]
			t = Table(data, [8 * cm, 3 * cm, 9 * cm], len(data) * [0.42 * cm])
			t.setStyle(TableStyle(global_format))
			elements.append(t)

		if Vacation_Line.commission != 0:
			data = [
				[Paragraph('Prom. Comisiones', style_left_tab_ter), Paragraph('{:,.2f}'.format(Vacation_Line.commission or 0.00), style_right),'']
			]
			t = Table(data, [8 * cm, 3 * cm, 9 * cm], len(data) * [0.42 * cm])
			t.setStyle(TableStyle(global_format))
			elements.append(t)

		if Vacation_Line.bonus != 0:
			data = [
				[Paragraph('Prom. Bonificacion', style_left_tab_ter), Paragraph('{:,.2f}'.format(Vacation_Line.bonus or 0.00), style_right),'']
			]
			t = Table(data, [8 * cm, 3 * cm, 9 * cm], len(data) * [0.42 * cm])
			t.setStyle(TableStyle(global_format))
			elements.append(t)

		if Vacation_Line.extra_hours != 0:
			data = [
				[Paragraph('Prom. Horas Extras', style_left_tab_ter), Paragraph('{:,.2f}'.format(Vacation_Line.extra_hours or 0.00), style_right),'']
			]
			t = Table(data, [8 * cm, 3 * cm, 9 * cm], len(data) * [0.42 * cm])
			t.setStyle(TableStyle(global_format))
			elements.append(t)

		data = [
			['',Paragraph('_______________<br/>%s' % ('{:,.2f}'.format(Vacation_Line.computable_remuneration or 0.00)), style_right),'']
		]
		t = Table(data, [8 * cm, 3 * cm, 9 * cm], len(data) * [0.42 * cm])
		t.setStyle(TableStyle(global_format))
		elements.append(t)

		if Last_Contract.labor_regime == 'general':
			data = [
				[Paragraph('<strong>- Vacaciones por Percibir</strong>', style_left_tab_seg),'','','',''],
			]
			t = Table(data, [8 * cm, 4 * cm, 2 * cm, 3 * cm,3 * cm], len(data) * [0.42 * cm])
			t.setStyle(TableStyle(global_format))
			elements.append(t)

			if Vacation_Line.months != 0:
				data = [
					[Paragraph('Por los %d mes(es)' % (Vacation_Line.months or 0), style_left_tab_ter),
					 Paragraph('%s / 12 * %d' % ('{:,.2f}'.format(Vacation_Line.computable_remuneration or 0.00),Vacation_Line.months or 0), style_left),'=',
					 Paragraph('{:,.2f}'.format(Vacation_Line.vacation_per_month or 0.00), style_right),'']
				]
				t = Table(data, [8 * cm, 4 * cm, 2 * cm, 3 * cm,3 * cm], len(data) * [0.42 * cm])
				t.setStyle(TableStyle(global_format))
				elements.append(t)

			if Vacation_Line.days != 0:
				data = [
					[Paragraph('Por los %d dia(s)' % (Vacation_Line.days or 0), style_left_tab_ter),
					 Paragraph('%s / 12 / 30 * %d' % ('{:,.2f}'.format(Vacation_Line.computable_remuneration or 0.00), Vacation_Line.days or 0), style_left), '=',
					 Paragraph('{:,.2f}'.format(Vacation_Line.vacation_per_day or 0.00), style_right), '']
				]
				t = Table(data, [8 * cm, 4 * cm, 2 * cm, 3 * cm,3 * cm], len(data) * [0.42 * cm])
				t.setStyle(TableStyle(global_format))
				elements.append(t)

			if Vacation_Line.advanced_vacation != 0:
				data = [
					[Paragraph('Vac. Adelantadas', style_left_tab_ter),
					 '', '=',
					 Paragraph('-{:,.2f}'.format(Vacation_Line.advanced_vacation or 0.00), style_right), '']
				]
				t = Table(data, [8 * cm, 4 * cm, 2 * cm, 3 * cm, 3 * cm], len(data) * [0.42 * cm])
				t.setStyle(TableStyle(global_format))
				elements.append(t)

			if Vacation_Line.accrued_vacation != 0:
				data = [
					[Paragraph('Vac. Devengadas', style_left_tab_ter),
					 '', '=',
					 Paragraph('{:,.2f}'.format(Vacation_Line.accrued_vacation or 0.00), style_right), '']
				]
				t = Table(data, [8 * cm, 4 * cm, 2 * cm, 3 * cm, 3 * cm], len(data) * [0.42 * cm])
				t.setStyle(TableStyle(global_format))
				elements.append(t)

			data = [
				['',
				 Paragraph('<strong>Total Vacac a Recibir</strong>', style_left), '= s/',
				 Paragraph('_______________<br/>{:,.2f}'.format(Vacation_Line.total_vacation or 0.00), style_right), '']
			]

			t = Table(data, [8 * cm, 4 * cm, 2 * cm, 3 * cm,3 * cm], len(data) * [0.42 * cm])
			t.setStyle(TableStyle(global_format))
			elements.append(t)
			elements.append(Spacer(2, 6))
			# elements.append(spacer)

		else:
			data = [
				[Paragraph('<strong>- Vacaciones por Percibir</strong>', style_left_tab_seg),'','','',''],
			]
			t = Table(data, [8 * cm, 4 * cm, 2 * cm, 3 * cm,3 * cm], len(data) * [0.42 * cm])
			t.setStyle(TableStyle(global_format))
			elements.append(t)

			if Vacation_Line.months != 0:
				data = [
					[Paragraph('Por los %d mes(es)' % (Vacation_Line.months or 0), style_left_tab_ter),
					 Paragraph('%s / 2 / 12 * %d' % ('{:,.2f}'.format(Vacation_Line.computable_remuneration or 0.00),Vacation_Line.months or 0), style_left),'=',
					 Paragraph('{:,.2f}'.format(Vacation_Line.vacation_per_month or 0.00), style_right),'']
				]
				t = Table(data, [8 * cm, 4 * cm, 2 * cm, 3 * cm,3 * cm], len(data) * [0.42 * cm])
				t.setStyle(TableStyle(global_format))
				elements.append(t)

			if Vacation_Line.days != 0:
				data = [
					[Paragraph('Por los %d dia(s)' % (Vacation_Line.days or 0), style_left_tab_ter),
					 Paragraph('%s / 2 / 12 / 30 * %d' % ('{:,.2f}'.format(Vacation_Line.computable_remuneration or 0.00), Vacation_Line.days or 0), style_left), '=',
					 Paragraph('{:,.2f}'.format(Vacation_Line.vacation_per_day or 0.00), style_right), '']
				]
				t = Table(data, [8 * cm, 4 * cm, 2 * cm, 3 * cm,3 * cm], len(data) * [0.42 * cm])
				t.setStyle(TableStyle(global_format))
				elements.append(t)

			if Vacation_Line.advanced_vacation != 0:
				data = [
					[Paragraph('Vac. Adelantadas', style_left_tab_ter),
					 '', '=',
					 Paragraph('-{:,.2f}'.format(Vacation_Line.advanced_vacation or 0.00), style_right), '']
				]
				t = Table(data, [8 * cm, 4 * cm, 2 * cm, 3 * cm, 3 * cm], len(data) * [0.42 * cm])
				t.setStyle(TableStyle(global_format))
				elements.append(t)

			if Vacation_Line.accrued_vacation != 0:
				data = [
					[Paragraph('Vac. Devengadas', style_left_tab_ter),
					 '', '=',
					 Paragraph('{:,.2f}'.format(Vacation_Line.accrued_vacation or 0.00), style_right), '']
				]
				t = Table(data, [8 * cm, 4 * cm, 2 * cm, 3 * cm, 3 * cm], len(data) * [0.42 * cm])
				t.setStyle(TableStyle(global_format))
				elements.append(t)

			data = [
				['',
				 Paragraph('<strong>Total Vacac a Recibir</strong>', style_left), '= s/',
				 Paragraph('_______________<br/>{:,.2f}'.format(Vacation_Line.total_vacation or 0.00), style_right), '']
			]

			t = Table(data, [8 * cm, 4 * cm, 2 * cm, 3 * cm,3 * cm], len(data) * [0.42 * cm])
			t.setStyle(TableStyle(global_format))
			elements.append(t)
			elements.append(Spacer(2, 6))
			# elements.append(spacer)

		data = [
			[Paragraph('<strong>4) RETENCIONES POR FONDO DE PENSIONES: *** "%s" ***</strong>' % Vacation_Line.membership_id.name, style_left_tab)]
		]

		t = Table(data, [20 * cm], len(data) * [0.42 * cm])
		t.setStyle(TableStyle(global_format))
		elements.append(t)

		data = [
			[Paragraph('Retencion a las Vacaciones Percibidas', style_left_tab_ter),'','=',
			 Paragraph('{:,.2f}'.format(-(Vacation_Line.onp+Vacation_Line.afp_jub+Vacation_Line.afp_si+Vacation_Line.afp_mixed_com+Vacation_Line.afp_fixed_com) or 0.00), style_right),''],
			['',
			 Paragraph('<strong>Total a Retener</strong>', style_left),'= s/',
			 Paragraph('_______________<br/>{:,.2f}'.format(-(Vacation_Line.onp+Vacation_Line.afp_jub+Vacation_Line.afp_si+Vacation_Line.afp_mixed_com+Vacation_Line.afp_fixed_com) or 0.00), style_right),'']
		]

		t = Table(data, [8 * cm, 4 * cm, 2 * cm, 3 * cm,3 * cm], len(data) * [0.42 * cm])
		t.setStyle(TableStyle(global_format))
		elements.append(t)
		elements.append(spacer)

		ExtraLine = self.env['hr.extra.concept'].search([('liquidation_id', '=', Liquidation.id), ('employee_id', '=', self.id)], limit=1)
		In_Concepts = ExtraLine.conceptos_lines.filtered(lambda c: c.type == 'in')
		Out_Concepts = ExtraLine.conceptos_lines.filtered(lambda c: c.type == 'out')
		in_data, out_data = [], []
		if In_Concepts:
			data = [
				[Paragraph('<strong>5) OTROS INGRESOS:</strong>', style_left_tab)]
			]

			t = Table(data, [20 * cm], len(data) * [0.42 * cm])
			t.setStyle(TableStyle(global_format))
			elements.append(t)

			for inc in In_Concepts:
				in_data.append([Paragraph('{0}'.format(inc.name_input_id.name.title()), style_left_tab_ter),'','=',
								Paragraph('{:,.2f}'.format(inc.amount or 0.00), style_right),''])
			# in_data += in_data
			in_data += [
				['',
				 Paragraph('<strong>Total Otros Ingresos</strong>', style_left),'= s/',
				 Paragraph('_______________<br/>{:,.2f}'.format(ExtraTotal.income or 0.00), style_right),'']
			]
			t = Table(in_data, [8 * cm, 4 * cm, 2 * cm, 3 * cm,3 * cm], len(in_data) * [0.42 * cm])
			t.setStyle(TableStyle(global_format))
			elements.append(t)
			elements.append(spacer)

		if Out_Concepts:
			data = [
				[Paragraph('<strong>6) OTROS DESCUENTOS:</strong>', style_left_tab)]
			]

			t = Table(data, [20 * cm], len(data) * [0.42 * cm])
			t.setStyle(TableStyle(global_format))
			elements.append(t)

			for ouc in Out_Concepts:
				out_data.append([Paragraph('{0}'.format(ouc.name_input_id.name.title()), style_left_tab_ter),'','=',
								Paragraph('{:,.2f}'.format(-ouc.amount or 0.00), style_right),''])
			# out_data += out_data
			out_data += [
				['',
				 Paragraph('<strong>Total Otros Descuentos</strong>', style_left),'= s/',
				 Paragraph('_______________<br/>{:,.2f}'.format(-ExtraTotal.expenses or 0.0), style_right),'']
			]
			t = Table(out_data, [8 * cm, 4 * cm, 2 * cm, 3 * cm,3 * cm], len(out_data) * [0.42 * cm])
			t.setStyle(TableStyle(global_format))
			elements.append(t)
			elements.append(spacer)

		data = [
			[],
			['',
			 Paragraph('<strong>IMPORTE A PAGAR</strong>', style_left),
			 Paragraph('<strong>= S/</strong>', style_center),
			 Paragraph('<strong>_______________<br/>%s<br/>_______________</strong>' % '{:,.2f}'.format(total or 0.00), style_right),
			 '']
		]
		t = Table(data, [8 * cm, 4 * cm, 2 * cm, 3 * cm, 3 * cm], len(data) * [0.42 * cm])
		t.setStyle(TableStyle(global_format))
		elements.append(t)
		elements.append(spacer)

		data = [
			[Paragraph('Recibi de la empresa %s, la suma de <strong>S/ %s</strong> (%s),\
						correspondiente a mis benificios sociales conforme a ley, firmo en señal de conformidad.' %(self.env.company.partner_id.name,str(total or 0.00),MainParameter.number_to_letter(total_income - total_discount)), style_left)]
			]
		t = Table(data, [20 * cm])
		t.setStyle(TableStyle(global_format))
		elements.append(t)

		I = ReportBase.create_image(MainParameter.signature, MainParameter.dir_create_file + 'signature.jpg', 140.0, 40.0)
		data = [
			[Paragraph('{0} {1} de {2} del {3}'.format(self.env.company.city or '',
													   Last_Contract.date_end.day,
													   MainParameter.get_month_name(Last_Contract.date_end.month),
													   Last_Contract.date_end.year), style_left)],
			['',I if I else ''],
			[Paragraph('<strong>______________________________________<br/>%s<br/>%s N° %s</strong>' % (
				self.name or '', self.type_document_id.name or '', self.identification_id or ''), style_center),
			 Paragraph('<strong>______________________________________<br/>%s<br/>%s N° %s</strong>' % (
				 MainParameter.reprentante_legal_id.name or '',
				 MainParameter.reprentante_legal_id.l10n_latam_identification_type_id.name or '',
				 MainParameter.reprentante_legal_id.vat or ''), style_center)],
		]
		t = Table(data, [10 * cm, 10 * cm], len(data) * [0.9 * cm])
		t.setStyle(TableStyle([
			('ALIGN', (0, 0), (-1, -1), 'CENTER'),
			('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
		]))
		elements.append(t)

		elements.append(PageBreak())

		return elements