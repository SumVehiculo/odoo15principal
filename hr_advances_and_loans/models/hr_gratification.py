# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError
from datetime import *
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, inch, landscape, A4
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_RIGHT, TA_LEFT

class HrGratification(models.Model):
	_inherit = 'hr.gratification'

	def import_advances(self):
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		if not MainParameter.grat_advance_id:
			raise UserError('No se ha configurado un tipo de adelanto para Gratificacion en Parametros Generales de la pestaña Gratificacion')
		log = ''
		Lot = self.payslip_run_id
		for line in self.line_ids:
			sql = """
				select sum(ha.amount) as amount,
				ha.employee_id
				from hr_advance ha
				inner join hr_advance_type hat on hat.id = ha.advance_type_id
				where ha.discount_date >= '{0}' and
					  ha.discount_date <= '{1}' and
					  ha.employee_id = {2} and
					  ha.state = 'not payed' and
					  hat.id = {3}
				group by ha.employee_id
				""".format(Lot.date_start, Lot.date_end, line.employee_id.id, MainParameter.grat_advance_id.id)
			self._cr.execute(sql)
			data = self._cr.dictfetchall()
			if data:
				line.advance_amount = data[0]['amount']
				line.total = line.total_grat + line.bonus_essalud - line.advance_amount - line.loan_amount
				log += '%s\n' % line.employee_id.name
			self.env['hr.advance'].search([('discount_date', '>=', Lot.date_start),
										   ('discount_date', '<=', Lot.date_end),
										   ('employee_id', '=', line.employee_id.id),
										   ('state', '=', 'not payed'),
										   ('advance_type_id.id', '=', MainParameter.grat_advance_id.id)]).turn_paid_out()

		if log:
			return self.env['popup.it'].get_message('Se importo adelantos a los siguientes empleados:\n' + log)
		else:
			return self.env['popup.it'].get_message('No se importo ningun adelanto')

	def import_loans(self):
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		if not MainParameter.grat_loan_id:
			raise UserError('No se ha configurado un tipo de prestamo para Gratificacion en Parametros Generales de la pestaña Gratificacion')
		log = ''
		Lot = self.payslip_run_id
		for line in self.line_ids:
			sql = """
				select sum(hll.amount) as amount,
				hll.employee_id
				from hr_loan_line hll
				inner join hr_loan_type hlt on hlt.id = hll.loan_type_id
				where hll.date >= '{0}' and
					  hll.date <= '{1}' and
					  hll.employee_id = {2} and
					  hll.validation = 'not payed' and
					  hlt.id = {3}
				group by hll.employee_id
				""".format(Lot.date_start, Lot.date_end, line.employee_id.id, MainParameter.grat_loan_id.id)
			self._cr.execute(sql)
			data = self._cr.dictfetchall()
			if data:
				line.loan_amount = data[0]['amount']
				line.total = line.total_grat + line.bonus_essalud - line.advance_amount - line.loan_amount
				log += '%s\n' % line.employee_id.name
			self.env['hr.loan.line'].search([('date', '>=', Lot.date_start),
											 ('date', '<=', Lot.date_end),
											 ('employee_id', '=', line.employee_id.id),
											 ('validation', '=', 'not payed'),
											 ('loan_type_id.id', '=', MainParameter.grat_loan_id.id)]).turn_paid_out()

		if log:
			return self.env['popup.it'].get_message('Se importo prestamos a los siguientes empleados:\n' + log)
		else:
			return self.env['popup.it'].get_message('No se importo ningun prestamo')

	def set_amounts(self, line_ids, Lot, MainParameter):
		super(HrGratification, self).set_amounts(line_ids, Lot, MainParameter)
		inp_adv = MainParameter.grat_advance_id.input_id
		# inp_loan = MainParameter.grat_loan_id.input_id
		for line in line_ids:
			Slip = Lot.slip_ids.filtered(lambda slip: slip.employee_id == line.employee_id)
			adv_line = Slip.input_line_ids.filtered(lambda inp: inp.input_type_id == inp_adv)
			# loan_line = Slip.input_line_ids.filtered(lambda inp: inp.input_type_id == inp_loan)
			adv_line.amount = line.advance_amount + line.loan_amount
			# loan_line.amount += line.loan_amount

class HrGratificationLine(models.Model):
	_inherit = 'hr.gratification.line'

	advance_amount = fields.Float(string='(-) Monto Adelanto')
	loan_amount = fields.Float(string='(-) Monto Prestamo')

	def compute_grati_line(self):
		super(HrGratificationLine, self).compute_grati_line()
		for record in self:
			record.total = record.total_grat + record.bonus_essalud - record.advance_amount - record.loan_amount

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

		if self.advance_amount:
			data += [[
				Paragraph('0701', style_left),
				Paragraph('Adelanto de Remuneracion', style_left), '',
				Paragraph('{:,.2f}'.format(self.advance_amount) or '0.00', style_right),
				'']]
		if self.loan_amount:
			data += [[
				Paragraph('0706', style_left),
				Paragraph('Prestamos al Personal', style_left), '',
				Paragraph('{:,.2f}'.format(self.loan_amount) or '0.00', style_right),
				'']]

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