# -*- coding:utf-8 -*-
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
import datetime
import base64

class hr_vacation_rest_wizard(models.TransientModel):
	_name='hr.vacation.rest.wizard'
	_description='Hr Vacation Rest Wizard'

	# employee_id = fields.Many2one('hr.employee','Empleado', default=lambda self: self.env['hr.employee'].sudo().search([('user_id','=',self.env.user.id)]) )

	employees_ids = fields.Many2many('hr.employee','rel_vacation_rest_employee','employee_id','report_id','Empleados')
	showall = fields.Boolean('Todos los Empleados',default=True)
	type_show =  fields.Selection([('pantalla','Pantalla'),('excel','Excel')],default='pantalla',string=u'Mostrar en', required=True)

	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	# fiscal_year_id = fields.Many2one('account.fiscal.year',string='Ejercicio',required=True)


	def make_vacation_rest(self):
		self.env['hr.vacation.rest'].get_vacation_employee(self.employees_ids,self.showall)
		if self.type_show =='pantalla':
			if self.showall:
				domain=[('company_id','=',self.env.company.id),('is_saldo_final','=',True)]
			else:
				domain=[('company_id','=',self.env.company.id),('is_saldo_final','=',True),('employee_id','in',self.employees_ids.ids)]
			c={
				'name': 'Saldos de Vacaciones',
				'type': 'ir.actions.act_window',
				'res_model': 'hr.vacation.rest',
				'view_type': 'form',
				'view_mode': 'tree',
				'views': [(self.env.ref('hr_vacations_it.hr_vacation_rest_tree_resumen').id, 'tree')],
				'search_view_id':[self.env.ref('hr_vacations_it.hr_vacation_rest_search').id, 'search'],
				'domain':domain
				}
			# print(c)
			return c
		elif self.type_show =='excel':
			if self.showall:
				domain=[('company_id','=',self.env.company.id)]
			else:
				domain=[('company_id','=',self.env.company.id),('employee_id','in',self.employees_ids.ids)]
			return self.get_excel(domain)

	def get_excel(self,domain):
		import io
		from xlsxwriter.workbook import Workbook
		if len(self.ids) > 1:
			raise UserError('No se puede seleccionar mas de un registro para este proceso')
		ReportBase = self.env['report.base']
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		directory = MainParameter.dir_create_file

		if not directory:
			raise UserError(u'No existe un Directorio de Descarga configurado en Parametros Principales de Nomina para su Compañía')

		workbook = Workbook(directory + 'Reporte_control_vacaciones.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		worksheet = workbook.add_worksheet("Reporte Control Vacaciones")
		worksheet.set_tab_color('blue')

		worksheet.merge_range(0, 0, 0, 7, "Empresa: %s" % self.company_id.partner_id.name or '', formats['especial2'])
		worksheet.merge_range(1, 0, 1, 7, "RUC: %s" % self.company_id.partner_id.vat or '', formats['especial2'])
		worksheet.merge_range(2, 0, 2, 7, "*** REPORTE DE SALDO DE VACACIONES ***", formats['especial5'])

		data = self.env['hr.vacation.rest'].search(domain)
		# print("data",data)
		x, y = 4, 0

		# estilo personalizado
		boldbord = workbook.add_format({'bold': True, 'font_name': 'Arial'})
		boldbord.set_border(style=1)
		boldbord.set_align('center')
		boldbord.set_align('vcenter')
		# boldbord.set_align('bottom')
		boldbord.set_text_wrap()
		boldbord.set_font_size(10)
		boldbord.set_bg_color('#99CCFF')

		dateformat = workbook.add_format({'num_format':'dd-mm-yyyy'})
		dateformat.set_align('center')
		dateformat.set_align('vcenter')
		# dateformat.set_border(style=1)
		dateformat.set_font_size(10)
		dateformat.set_font_name('Times New Roman')

		formatCenter = workbook.add_format(
			{'num_format': '0.00', 'font_name': 'Arial', 'align': 'center', 'font_size': 10})
		formatLeft = workbook.add_format(
			{'num_format': '0.00', 'font_name': 'Arial', 'align': 'left', 'font_size': 10})
		numberdos = workbook.add_format(
			{'num_format': '0.00', 'font_name': 'Arial', 'align': 'right'})
		numberdos.set_font_size(10)
		styleFooterSum = workbook.add_format(
			{'bold': True, 'num_format': '0.00', 'font_name': 'Arial', 'align': 'right', 'font_size': 11, 'top': 1, 'bottom': 2})
		styleFooterSum.set_bottom(8)

		HEADERS = ['Fecha de Aplicacion','Año','N° de Ident.','Periodo Inicio','Periodo Fin','Motivo','Dias Ganados','Dias Gozados','Saldo de Dias']
		worksheet = ReportBase.get_headers(worksheet,HEADERS,x,y,boldbord)
		x += 1

		cont = 0
		cuenta = ''
		totals = [0] * 3
		saldo = 0
		limiter = 6

		for c, line in enumerate(data, 1):
			employee = line.employee_id
			if cont == 0:
				cuenta = employee.name
				# print("cuenta",cuenta)
				cont += 1
				worksheet.merge_range(x, 0, x, 4, 'Empleado: ' + str(cuenta) if employee.name else '', formats['especial2'])
				x += 1

			if cuenta != employee.name:
				worksheet.write(x, limiter - 1, 'Total ', formats['especial2'])
				for total in totals:
					worksheet.write(x, limiter, total, styleFooterSum)
					limiter += 1

				x += 2
				totals = [0] * 3
				saldo = 0
				limiter = 6

				cuenta = employee.name
				worksheet.merge_range(x, 0, x, 4, 'Empleado: ' + str(cuenta) if employee.name else '', formats['especial2'])
				x += 1

			saldo = saldo + (line.days if line.days > 0 else (line.days_rest if line.internal_motive == 'rest' else 0)) - ((line.days)*-1 if line.days < 0 else 0)
			worksheet.write(x, 0, line.date_aplication if line.date_aplication else '', dateformat)
			worksheet.write(x, 1, line.year if line.year else '', formatLeft)
			worksheet.write(x, 2, line.identification_id if line.identification_id else '', formatLeft)
			worksheet.write(x, 3, line.date_from if line.date_from else '', dateformat)
			worksheet.write(x, 4, line.date_end if line.date_end else '', dateformat)
			worksheet.write(x, 5, line.motive if line.motive else '', formatLeft)
			worksheet.write(x, 6, line.days if line.days > 0 else (line.days_rest if line.internal_motive == 'rest' else 0), numberdos)
			worksheet.write(x, 7, (line.days)*-1 if line.days < 0 else '', numberdos)
			worksheet.write(x, 8, saldo, numberdos)

			totals[0] += (line.days if line.days > 0 else (line.days_rest if line.internal_motive == 'rest' else 0))
			totals[1] += ((line.days)*-1 if line.days < 0 else 0)
			totals[2] = totals[0]-totals[1]

			x += 1

		worksheet.write(x, limiter - 1, 'Total ', formats['especial2'])
		for total in totals:
			worksheet.write(x, limiter, total, styleFooterSum)
			limiter += 1

		widths = [16, 15, 18, 16, 16, 50, 14, 14, 14]
		worksheet = ReportBase.resize_cells(worksheet, widths)
		workbook.close()
		f = open(directory + 'Reporte_control_vacaciones.xlsx', 'rb')
		return self.env['popup.it'].get_file('Reporte Control Vacaciones.xlsx', base64.encodebytes(b''.join(f.readlines())))