# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError
import base64

class ReportCuentaCorriente(models.TransientModel):
	_name = "report.cuenta.corriente"
	_description = "Reporte Cuenta Corriente"

	name = fields.Char()
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	# type_show =  fields.Selection([('pantalla','Pantalla'),('excel','Excel'),('pdf','PDF')],default='pantalla',string=u'Mostrar en', required=True)
	# payslip_run_id = fields.Many2one('hr.payslip.run', string='Periodo')
	employees_ids = fields.Many2many('hr.employee','rel_cuenta_corriente_employee','employee_id','report_id','Empleados')
	allemployees = fields.Boolean('Todos los Empleados',default=True)

	# @api.model
	# def default_get(self, fields):
	# 	res = super(ReportVidaLey, self).default_get(fields)
	# 	payslip_run_id = res.get('payslip_run_id')
	# 	res.update({'payslip_run_id': payslip_run_id})
	# 	return res

	# @api.onchange('allemployees')
	# def onchange_allemployees(self):
	# 	if self.allemployees==False:
	# 		employee_ids = []
	# 		for employe in self.payslip_run_id.slip_ids:
	# 			employee_ids.append(employe.employee_id.id)
	# 		# print("employee_ids",employee_ids)
	# 		domain = {"employees_ids": [("id", "in", employee_ids)]}
	# 		return {"domain": domain}

	def get_all(self):
		# self.domain_dates()
		option=0
		return self.get_excel(option)

	def get_journals(self):
		# self.domain_dates()
		if self.allemployees == False:
			option=1
			return self.get_excel(option)
		else:
			raise UserError('Debe escoger al menos un Empleado.')

	def _get_sql(self,option):
		sql_employees = "where T.employee_id in (%s) " % (','.join(str(i) for i in self.employees_ids.ids)) if option == 1 else ""
		sql = """
		select T.employee_id,
			T.date,T.trabajador,
			T.dni, T.departamento,
			T.saldo_ini,
			T.amortizacion,
			coalesce((T.saldo_ini-T.amortizacion),0) as saldo_fin,
			T.code,
			T.concepto
		from (
		select T.employee_id,
				T.date,T.trabajador,
				T.dni, T.departamento,
				avg(T.saldo_ini) as saldo_ini,
				sum(T.amortizacion) as amortizacion,
				T.code,
				T.concepto
			from (
			select he.id as employee_id,
					hl.date,
					he.name as trabajador,
					he.identification_id as dni,
					hd.name as departamento,
					avg(hl.amount) as saldo_ini,
					CASE WHEN hll.validation = 'paid out' THEN sum(hll.amount) ELSE 0 END AS amortizacion,
					hpit.code,
					hpit.name as concepto
				from hr_loan hl
				inner join hr_loan_line hll on hll.loan_id = hl.id
				inner join hr_employee he on he.id = hl.employee_id
				left join hr_loan_type hlt on hlt.id = hl.loan_type_id
				left join hr_payslip_input_type hpit on hpit.id = hlt.input_id
				left join hr_department hd on hd.id = he.department_id
--				left join res_partner rp on rp.id = he.address_id
--				left join res_country_state rcs on rcs.id= rp.province_id
				where hl.company_id = {company}
				group by he.id,hl.date,he.name, he.identification_id,hll.validation,hd.name, hpit.code,hpit.name
				)T
				group by T.employee_id,T.date,T.trabajador, T.dni,T.departamento,T.code,T.concepto
		union all
		
		select he.id as employee_id,
				ha.date,
				he.name as trabajador,
				he.identification_id as dni,
				hd.name as departamento,
				ha.amount as saldo_ini,
				CASE WHEN ha.state = 'paid out' THEN ha.amount ELSE 0 END AS amortizacion,
				hpit.code,
				hpit.name as concepto
			from hr_advance ha
			inner join hr_employee he on he.id = ha.employee_id
			left join hr_advance_type hat on hat.id = ha.advance_type_id
			left join hr_payslip_input_type hpit on hpit.id = hat.input_id
			left join hr_department hd on hd.id = he.department_id
--			left join res_partner rp on rp.id = he.address_id
--			left join res_country_state rcs on rcs.id= rp.province_id
			where ha.company_id = {company}
		) T
		{sql_employees}
		order by T.trabajador,T.date
		""".format(
				company = self.company_id.id,
				sql_employees = sql_employees
			)
		return sql

	def get_excel(self,option):
		import io
		from xlsxwriter.workbook import Workbook
		if len(self.ids) > 1:
			raise UserError('No se puede seleccionar mas de un registro para este proceso')
		ReportBase = self.env['report.base']
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		directory = MainParameter.dir_create_file

		if not directory:
			raise UserError(u'No existe un Directorio de Descarga configurado en Parametros Principales de Nomina para su Compañía')

		workbook = Workbook(directory + 'Reporte_cuenta_corriente.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		worksheet = workbook.add_worksheet("Reporte Cuenta Corriente")
		worksheet.set_tab_color('blue')

		worksheet.merge_range(0, 0, 0, 7, "Empresa: %s" % self.company_id.partner_id.name or '', formats['especial2'])
		worksheet.merge_range(1, 0, 1, 7, "RUC: %s" % self.company_id.partner_id.vat or '', formats['especial2'])
		worksheet.merge_range(2, 0, 2, 7, "Direccion: %s" % self.company_id.partner_id.street or '', formats['especial2'])
		worksheet.merge_range(3, 1, 3, 8, "*** REPORTE CUENTA CORRIENTE ***", formats['especial5'])

		self._cr.execute(self._get_sql(option))
		data = self._cr.dictfetchall()
		# print("data",data)
		x, y = 5, 0

		# estilo personalizado
		boldbord = workbook.add_format({'bold': True, 'font_name': 'Arial'})
		boldbord.set_border(style=1)
		boldbord.set_align('center')
		boldbord.set_align('vcenter')
		# boldbord.set_align('bottom')
		boldbord.set_text_wrap()
		boldbord.set_font_size(8)
		boldbord.set_bg_color('#99CCFF')

		dateformat = workbook.add_format({'num_format':'dd-mm-yyyy'})
		dateformat.set_align('center')
		dateformat.set_align('vcenter')
		# dateformat.set_border(style=1)
		dateformat.set_font_size(8)
		dateformat.set_font_name('Times New Roman')

		formatCenter = workbook.add_format(
			{'num_format': '0.00', 'font_name': 'Arial', 'align': 'center', 'font_size': 8})
		formatLeft = workbook.add_format(
			{'num_format': '0.00', 'font_name': 'Arial', 'align': 'left', 'font_size': 8})
		numberdos = workbook.add_format(
			{'num_format': '0.00', 'font_name': 'Arial', 'align': 'right'})
		numberdos.set_font_size(8)
		styleFooterSum = workbook.add_format(
			{'bold': True, 'num_format': '0.00', 'font_name': 'Arial', 'align': 'right', 'font_size': 9, 'top': 1, 'bottom': 2})
		styleFooterSum.set_bottom(6)

		HEADERS = ['Fecha','Trabajador','DNI','Area','Saldo Inicial','Amortizacion','Saldo Final','Codigo Concepto','Concepto']
		worksheet = ReportBase.get_headers(worksheet,HEADERS,x,y,boldbord)
		x += 1

		cont = 0
		cuenta = ''
		totals = [0] * 3
		limiter = 4


		for c, line in enumerate(data, 1):
			if cont == 0:
				cuenta = line['trabajador']
				# print("cuenta",cuenta)
				cont += 1
				worksheet.merge_range(x,0,x,4, 'Empleado: ' + str(cuenta) if line['trabajador'] else '',formats['especial2'])
				x += 1

			if cuenta != line['trabajador']:
				worksheet.write(x, limiter-1, 'Total ', formats['especial2'])
				for total in totals:
					worksheet.write(x, limiter, total, styleFooterSum)
					limiter += 1

				x += 1
				totals = [0] * 3
				limiter = 4

				cuenta = line['trabajador']
				worksheet.merge_range(x,0,x,4, 'Empleado: ' + str(cuenta) if line['trabajador'] else '',formats['especial2'])
				x += 1

			worksheet.write(x, 0, line['date'] if line['date'] else '', dateformat)
			worksheet.write(x, 1, line['trabajador'] if line['trabajador'] else '', formatLeft)
			worksheet.write(x, 2, line['dni'] if line['dni'] else '', formatCenter)
			worksheet.write(x, 3, line['departamento'] if line['departamento'] else '', formatLeft)
			worksheet.write(x, 4, line['saldo_ini'] if line['saldo_ini'] else 0.0, numberdos)
			worksheet.write(x, 5, line['amortizacion'] if line['amortizacion'] else 0.0, numberdos)
			worksheet.write(x, 6, line['saldo_fin'] if line['saldo_fin'] else 0.0, numberdos)
			worksheet.write(x, 7, line['code'] if line['code'] else '', formatCenter)
			worksheet.write(x, 8, line['concepto'] if line['concepto'] else '', formatLeft)

			totals[0] += line['saldo_ini']
			totals[1] += line['amortizacion']
			totals[2] += line['saldo_fin']

			x += 1

		worksheet.write(x, limiter-1, 'Total ', formats['especial2'])
		for total in totals:
			worksheet.write(x, limiter, total, styleFooterSum)
			limiter += 1

		widths = [13, 30, 14, 13, 13, 13, 13, 14, 25]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()
		f = open(directory + 'Reporte_cuenta_corriente.xlsx', 'rb')
		return self.env['popup.it'].get_file('Reporte Cuenta Corriente.xlsx', base64.encodebytes(b''.join(f.readlines())))