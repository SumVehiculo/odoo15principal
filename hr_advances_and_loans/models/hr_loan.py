from odoo import api, fields, models, tools
import calendar
from datetime import *
from decimal import *
from odoo.osv import osv
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError
import base64
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.pagesizes import letter, inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_RIGHT, TA_LEFT

class HrLoanType(models.Model):
	_name = 'hr.loan.type'
	_description = 'Loan Type'

	name = fields.Char(string='Nombre')
	input_id = fields.Many2one('hr.payslip.input.type', string='Input de Planillas')
	# salary_rule_id = fields.Many2one('hr.salary.rule', string='Concepto Remunerativo')
	company_id = fields.Many2one('res.company', string='Compañia', default=lambda self: self.env.company.id)

class HrLoan(models.Model):
	_name = 'hr.loan'
	_description = 'Loan'

	name = fields.Char()
	company_id = fields.Many2one('res.company', string='Compañia', default=lambda self: self.env.company.id, required=True)
	employee_id = fields.Many2one('hr.employee', string='Empleado')
	date = fields.Date(string='Fecha de Prestamo')
	amount = fields.Float(string='Monto de Prestamo')
	loan_type_id = fields.Many2one('hr.loan.type', string='Tipo de Prestamo')
	fees_number = fields.Integer(string='Numero de Cuotas')
	line_ids = fields.One2many('hr.loan.line', 'loan_id')
	observations = fields.Text(string='Observaciones')

	saldo_final = fields.Float(string='Saldo Final', readonly=True, compute='_compute_saldo_final')

	@api.depends('line_ids.amount','line_ids.validation')
	def _compute_saldo_final(self):
		for cuota in self:
			suma_total = 0.0
			for line in cuota.line_ids:
				if line.validation == 'not payed':
					suma_total += line.amount
			cuota.saldo_final = suma_total

	@api.onchange('employee_id', 'loan_type_id')
	def _get_name(self):
		for record in self:
			if record.employee_id and record.loan_type_id:
				record.name = '%s %s' % (record.loan_type_id.name, record.employee_id.name)

	def unlink(self):
		for loan in self:
			if loan.saldo_final != loan.amount:
				raise UserError("No puedes eliminar un prestamo que ya fue Aplicado.")
		return super(HrLoan, self).unlink()

	def get_fees(self):
		self.line_ids.unlink()
		ReportBase = self.env['report.base']
		date = self.date
		debt = self.amount
		for c, fee in enumerate(range(self.fees_number), 1):
			last_day = calendar.monthrange(date.year,date.month)[1]
			# print("last_day",last_day)
			if c == 1 and date.day == last_day:
				date = date
			if c != 1:
				date = date + relativedelta(months=1)
				# print("date",date)
			last_day = calendar.monthrange(date.year,date.month)[1]
			date = date.replace(day=last_day)
			fee_amount = ReportBase.custom_round(self.amount/self.fees_number, 2)
			debt -= fee_amount
			self.env['hr.loan.line'].create({
					'loan_id':self.id,
					'fee':c,
					'amount':fee_amount,
					'date':date,
					'debt':debt,
					'loan_type_id':self.loan_type_id.id
				})
		return self.env['popup.it'].get_message('Se calculo Correctamente')

	def refresh_fees(self):
		total = self.amount
		for line in self.line_ids.sorted(lambda l: l.fee):
			total -= line.amount
			line.debt = total
		self.fees_number = len(self.line_ids)

	def get_excel(self):
		import io
		from xlsxwriter.workbook import Workbook
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		ReportBase = self.env['report.base']
		if not MainParameter.dir_create_file:
			raise UserError('Falta configurar un directorio de descargas en Parametros Principales')
		route = MainParameter.dir_create_file
		workbook = Workbook(route + 'prestamos.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		##########ASISTENCIAS############
		worksheet = workbook.add_worksheet("PRESTAMOS")
		worksheet.set_tab_color('blue')

		worksheet.merge_range(1,0,1,4,"PRESTAMO %s %s"%(self.employee_id.name,self.date),formats['especial3'])
		worksheet.write(3,0,"Empleado",formats['boldbord'])
		worksheet.merge_range(3,1,3,2,self.employee_id.name,formats['especial1'])
		worksheet.write(3,3,"Fecha de Prestamo",formats['boldbord'])
		worksheet.write(3,4,self.date,formats['reverse_dateformat'])
		worksheet.write(5,0,"Tipo de Prestamo",formats['boldbord'])
		worksheet.merge_range(5,1,5,2,self.loan_type_id.name,formats['especial1'])
		worksheet.write(5,3,"Numero de Cuotas",formats['boldbord'])
		worksheet.write(5,4,self.fees_number,formats['especial1'])

		x = 7
		worksheet.write(x,0,"CUOTA",formats['boldbord'])
		worksheet.write(x,1,"MONTO",formats['boldbord'])
		worksheet.write(x,2,"FECHA DE PAGO",formats['boldbord'])
		worksheet.write(x,3,"DEUDA POR PAGAR",formats['boldbord'])
		worksheet.write(x,4,"VALIDACION",formats['boldbord'])
		x=8

		for line in self.line_ids:
			worksheet.write(x,0,line.fee if line.fee else 0,formats['numberdos'])
			worksheet.write(x,1,line.amount if line.amount else 0,formats['numberdos'])
			worksheet.write(x,2,line.date if line.date else '',formats['reverse_dateformat'])
			worksheet.write(x,3,line.debt if line.debt else 0,formats['numberdos'])
			worksheet.write(x,4,dict(line._fields['validation'].selection).get(line.validation) if line.validation else '',formats['especial1'])
			x += 1

		widths = [12,12,12,12,12,12]
		worksheet = ReportBase.resize_cells(worksheet, widths)
		workbook.close()

		f = open(route + 'prestamos.xlsx', 'rb')
		return self.env['popup.it'].get_file('Prestamo - %s.xlsx' % self.date, base64.encodebytes(b''.join(f.readlines())))

	def get_pdf(self):
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		ReportBase = self.env['report.base']
		if not MainParameter.dir_create_file:
			raise UserError('Falta configurar un directorio de descargas en Parametros Principales')
		route = MainParameter.dir_create_file
		doc = SimpleDocTemplate(route + 'prestamos.pdf',pagesize=letter, rightMargin=40,leftMargin=40, topMargin=40,bottomMargin=30)
		elements = []

		style_cell = ParagraphStyle(name='Center', alignment=TA_CENTER, fontSize=9.6, fontName="times-roman")
		simple_style = [('ALIGN', (0, 0), (-1, -1), 'CENTER'),
						('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]
		spacer = Spacer(10, 20)

		#Estilos
		style_title = ParagraphStyle(name='Center', alignment=TA_CENTER, fontSize=12, fontName="Helvetica-Bold")
		style_form = ParagraphStyle(name='Justify', alignment=TA_JUSTIFY, fontSize=10, fontName="Helvetica")
		style_left = ParagraphStyle(name='Left', alignment=TA_LEFT, fontSize=9.0, fontName="Helvetica")
		style_right = ParagraphStyle(name='Right', alignment=TA_RIGHT, fontSize=9.0, fontName="Helvetica")
		style_center = ParagraphStyle(name='Center', alignment=TA_CENTER, fontSize=9.0, fontName="Helvetica")

		I = ReportBase.create_image(self.env.company.logo, MainParameter.dir_create_file + 'logo.jpg', 125.0, 35.0)
		data = [
			[I if I else '',
			 Paragraph('<strong>%s</strong>' % self.company_id.name or '', style_left),
			 Paragraph('<strong>Fecha: %s </strong>' % str(datetime.strftime((self.date),'%d-%m-%Y')) or '', style_center)],
			['', Paragraph('<strong>R.U.C.: %s </strong>' % self.company_id.vat or '', style_left)],
		]
		t = Table(data, [5 * cm, 9 * cm, 6 * cm],len(data) * [0.5 * cm])
		t.setStyle(TableStyle([
			('SPAN', (0, 0), (0, -1)),
			('ALIGN', (0, 0), (0, 0), 'CENTER'),
			('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),]))
		elements.append(t)
		elements.append(spacer)

		elements.append(Paragraph("AUTORIZACION DE DESCUENTOS SOBRE REMUNERACIONES POR PRESTAMO AL TRABAJADOR", style_title))
		elements.append(spacer)

		data = [[Paragraph('RECIBO POR PRESTAMO', style_left),
				 Paragraph("VALOR S/", style_left),
				 Paragraph('{:,.2f}'.format(self.amount) if self.amount else '0.00', style_right)],
				]
		t = Table(data, [12 * cm, 3 * cm, 3 * cm],len(data) * [0.6 * cm])
		t.setStyle(TableStyle([
						('ALIGN', (0, 0), (-1, -1), 'CENTER'),
						('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
						('BOX', (2, 0), (-1, -1), 0.25, colors.black),
			]))
		elements.append(t)
		elements.append(spacer)
		elements.append(spacer)

		# conversion de numero a letras
		number = self.amount
		UNIDADES = (
			'',
			'UN ',
			'DOS ',
			'TRES ',
			'CUATRO ',
			'CINCO ',
			'SEIS ',
			'SIETE ',
			'OCHO ',
			'NUEVE ',
			'DIEZ ',
			'ONCE ',
			'DOCE ',
			'TRECE ',
			'CATORCE ',
			'QUINCE ',
			'DIECISEIS ',
			'DIECISIETE ',
			'DIECIOCHO ',
			'DIECINUEVE ',
			'VEINTE '
		)

		DECENAS = (
			'VENTI',
			'TREINTA ',
			'CUARENTA ',
			'CINCUENTA ',
			'SESENTA ',
			'SETENTA ',
			'OCHENTA ',
			'NOVENTA ',
			'CIEN '
		)

		CENTENAS = (
			'CIENTO ',
			'DOSCIENTOS ',
			'TRESCIENTOS ',
			'CUATROCIENTOS ',
			'QUINIENTOS ',
			'SEISCIENTOS ',
			'SETECIENTOS ',
			'OCHOCIENTOS ',
			'NOVECIENTOS '
		)

		MONEDAS = (
			{'country': u'Colombia', 'currency': 'COP', 'singular': u'PESO COLOMBIANO',
			 'plural': u'PESOS COLOMBIANOS',
			 'symbol': u'$'},
			{'country': u'Estados Unidos', 'currency': 'USD', 'singular': u'DÓLAR', 'plural': u'DÓLARES',
			 'symbol': u'US$'},
			{'country': u'Europa', 'currency': 'EUR', 'singular': u'EURO', 'plural': u'EUROS', 'symbol': u'€'},
			{'country': u'México', 'currency': 'MXN', 'singular': u'PESO MEXICANO', 'plural': u'PESOS MEXICANOS',
			 'symbol': u'$'},
			{'country': u'Perú', 'currency': 'PEN', 'singular': u'SOL', 'plural': u'SOLES', 'symbol': u'S/.'},
			{'country': u'Reino Unido', 'currency': 'GBP', 'singular': u'LIBRA', 'plural': u'LIBRAS',
			 'symbol': u'£'}
		)

		# Para definir la moneda me estoy basando en los código que establece el ISO 4217
		# Decidí poner las variables en inglés, porque es más sencillo de ubicarlas sin importar el país
		# Si, ya sé que Europa no es un país, pero no se me ocurrió un nombre mejor para la clave.

		def __convert_group(n):
			"""Turn each group of numbers into letters"""
			output = ''

			if (n == '100'):
				output = "CIEN"
			elif (n[0] != '0'):
				output = CENTENAS[int(n[0]) - 1]

			k = int(n[1:])
			if (k <= 20):
				output += UNIDADES[k]
			else:
				if ((k > 30) & (n[2] != '0')):
					output += '%sY %s' % (DECENAS[int(n[1]) - 2], UNIDADES[int(n[2])])
				else:
					output += '%s%s' % (DECENAS[int(n[1]) - 2], UNIDADES[int(n[2])])
			return output

		# raise osv.except_osv('Alerta', number)
		number = str(round(float(number), 2))
		separate = number.split(".")
		number = int(separate[0])
		mi_moneda = 'PEN'
		if mi_moneda != None:
			try:
				moneda = ""
				for moneda1 in MONEDAS:
					if moneda1['currency'] == mi_moneda:
						# moneda = ifilter(lambda x: x['currency'] == mi_moneda, MONEDAS).next()
						# return "Tipo de moneda inválida"
						if number < 2:
							# raise osv.except_osv('Alerta', number)
							if float(number) == 0:
								moneda = moneda1['plural']
							else:
								if int(separate[1]) > 0:
									moneda = moneda1['plural']
								else:
									moneda = moneda1['singular']
						else:
							moneda = moneda1['plural']
			except:
				return "Tipo de moneda inválida"
		else:
			moneda = ""

		if int(separate[1]) >= 0:
			moneda = "con " + str(separate[1]).ljust(2, '0') + "/" + "100 " + moneda

		"""Converts a number into string representation"""
		converted = ''

		if not (0 <= number < 999999999):
			raise osv.except_osv('Alerta', number)
		# return 'No es posible convertir el numero a letras'

		number_str = str(number).zfill(9)
		millones = number_str[:3]
		miles = number_str[3:6]
		cientos = number_str[6:]

		if (millones):
			if (millones == '001'):
				converted += 'UN MILLON '
			elif (int(millones) > 0):
				converted += '%sMILLONES ' % __convert_group(millones)

		if (miles):
			if (miles == '001'):
				converted += 'MIL '
			elif (int(miles) > 0):
				converted += '%sMIL ' % __convert_group(miles)

		if (cientos):
			if (cientos == '001'):
				converted += 'UN '
			elif (int(cientos) > 0):
				converted += '%s ' % __convert_group(cientos)
		if float(number_str) == 0:
			converted += 'CERO '
		converted += moneda
		name_num = converted.upper()

		text = u"""Yo, {name}, identificado(a) con {tipo_doc} N° {identification_id}, recibi la
						suma de S/ {amount} ({name_num}), por concepto de prestamo o mutuo
						sin intereses el dia {date}, de la empresa {company}.<br /><br />
						Por lo anterior, autorizo al pagador de la empresa para que descuente de mis haberes de la 
						siguiente forma:<br /><br />
					""".format(
			name = self.employee_id.name,
			tipo_doc= self.employee_id.type_document_id.name,
			identification_id = self.employee_id.identification_id,
			amount = self.amount,
			name_num = name_num or '',
			date = str(datetime.strftime((self.date),'%d-%m-%Y')) or '',
			company = self.company_id.name,
		)
		elements.append(Paragraph(text, style_form))


		data = [[Paragraph('CUOTA', style_cell),
				Paragraph('MONTO', style_cell),
				Paragraph('FECHA DE PAGO', style_cell),
				Paragraph('DEUDA POR PAGAR', style_cell),
				Paragraph('VALIDACION', style_cell)],
				]
		y = 1
		for line in self.line_ids:
			data.append([
						Paragraph(str(line.fee) if line.fee else '', style_cell),
						Paragraph(str(line.amount) if line.amount else '0', style_cell),
						Paragraph(str(datetime.strftime((line.date),'%d-%m-%Y')) if line.date else '', style_cell),
						Paragraph(str(line.debt) if line.debt else '0', style_cell),
						Paragraph(dict(line._fields['validation'].selection).get(line.validation) if line.validation else '', style_cell)
					])
			y += 1
		t = Table(data, [0.8*inch, 1.0*inch, 1.4*inch, 1.4*inch, 1.4*inch], y*[0.3*inch])
		t.setStyle(TableStyle([
							('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#B0B0B0")),
							('ALIGN', (0, 0), (-1, -1), 'CENTER'),
							('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
							('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
							('BOX', (0, 0), (-1, -1), 0.25, colors.black),
							]))
		elements.append(t)
		elements.append(spacer)

		text = u"""Asimismo, autorizo expresamente al empleador que, retenga y cobre de mi liquidacion de
						Beneficios Sociales los saldos que adeude, si llegase a finalizar mi contrato de trabajo antes 
						de completar el pago total de este prestamo.<br /><br /><br />
						Recibi Conforme:
					"""
		elements.append(Paragraph(text, style_form))

		elements.append(spacer)
		elements.append(spacer)

		I = ReportBase.create_image(MainParameter.signature, MainParameter.dir_create_file + 'signature.jpg', 160.0, 35.0)
		dataf = [
			[I if I else '', '', ''],
			[self.company_id.name or '', '', self.employee_id.name],
			['EMPLEADOR', '', "DNI: %s" % self.employee_id.identification_id or ''],
			['', '', 'TRABAJADOR(A)'],
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
		elements.append(spacer)
		elements.append(spacer)
		elements.append(spacer)

		text = u"""Aprobado por ____________________________ <br /><br />
				   Entrega del prestamo o mutuo a travez del (cheque, transferencia, efectivo) N° ____________
					"""
		elements.append(Paragraph(text, style_form))

		doc.build(elements)
		f = open(route + 'prestamos.pdf', 'rb')
		return self.env['popup.it'].get_file('Prestamo %s - %s.pdf' % (self.employee_id.name, self.date), base64.encodebytes(b''.join(f.readlines())))


class HrLoanLine(models.Model):
	_name = 'hr.loan.line'
	_description = 'Loan Line'

	loan_id = fields.Many2one('hr.loan', ondelete='cascade')
	employee_id = fields.Many2one(related='loan_id.employee_id', store=True)
	# input_id = fields.Many2one(related='loan_id.loan_type_id.input_id', store=True)
	loan_type_id = fields.Many2one('hr.loan.type', string='Tipo de Prestamo')
	fee = fields.Integer(string='Cuota')
	amount = fields.Float(string='Monto')
	date = fields.Date(string='Fecha de Pago')
	debt = fields.Float(string='Deuda por Pagar')
	validation = fields.Selection([('not payed', 'NO PAGADO'), ('paid out', 'PAGADO')], string='Validacion', default='not payed')

	def turn_paid_out(self):
		for record in self:
			record.validation = 'paid out'

	def set_not_payed(self):
		for record in self:
			record.validation = 'not payed'