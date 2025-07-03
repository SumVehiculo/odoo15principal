# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError
import base64

class ReportDerechohabientes(models.TransientModel):
	_name = "report.derechohabientes"
	_description = "Reporte Derechohabientes"

	name = fields.Char()
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	# type_show =  fields.Selection([('pantalla','Pantalla'),('excel','Excel'),('pdf','PDF')],default='pantalla',string=u'Mostrar en', required=True)
	# payslip_run_id = fields.Many2one('hr.payslip.run', string='Periodo')
	employees_ids = fields.Many2many('hr.employee','rel_reporte_derechohabientes_employee','employee_id','report_id','Empleados')
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

		workbook = Workbook(directory + 'Reporte_derechohabientes.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		worksheet = workbook.add_worksheet("Reporte Derechohabientes")
		worksheet.set_tab_color('blue')

		worksheet.merge_range(0, 0, 0, 7, "Empresa: %s" % self.company_id.partner_id.name or '', formats['especial2'])
		worksheet.merge_range(1, 0, 1, 7, "RUC: %s" % self.company_id.partner_id.vat or '', formats['especial2'])
		worksheet.merge_range(2, 0, 2, 7, "Direccion: %s" % self.company_id.partner_id.street or '', formats['especial2'])
		worksheet.merge_range(3, 1, 3, 6, "*** REPORTE DE DERECHOHABIENTES ***", formats['especial5'])

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

		formatCenter = workbook.add_format({'num_format': '0.00', 'font_name': 'Arial', 'align': 'center', 'font_size': 8})
		formatLeft = workbook.add_format({'num_format': '0.00', 'font_name': 'Arial', 'align': 'left', 'font_size': 8})
		numberdos = workbook.add_format({'num_format': '0.00', 'font_name': 'Arial', 'align': 'right'})
		numberdos.set_font_size(8)
		styleFooterSum = workbook.add_format({'bold': True, 'num_format': '0.00', 'font_name': 'Arial', 'align': 'right', 'font_size': 9, 'top': 1, 'bottom': 2})
		styleFooterSum.set_bottom(6)

		HEADERS = ['Apellidos y Nombres','Tipo de Documento','N° Documento','Parentesco','Fecha Nacimiento','Edad','Cursando Estudios']
		worksheet = ReportBase.get_headers(worksheet,HEADERS,x,y,boldbord)
		x += 1

		if option == 1:
			# print("employees_ids",tuple(self.employees_ids.mapped('id')))
			employees = self.env['hr.derechohabientes'].search([('employee_id','in',tuple(self.employees_ids.mapped('id')))], order='employee_id')
		else:
			employees = self.env['hr.derechohabientes'].search([], order='employee_id')

		cont = 0
		cuenta = ''

		for line in employees:
			if cont == 0:
				cuenta = line.employee_id.name
				# print("cuenta",cuenta)
				cont += 1
				worksheet.merge_range(x,0,x,4, 'Empleado: ' + str(cuenta) if line.employee_id else '',formats['especial2'])
				x += 1

			if cuenta != line.employee_id.name:
				x += 1

				cuenta = line.employee_id.name
				worksheet.merge_range(x,0,x,4, 'Empleado: ' + str(cuenta) if line.employee_id else '',formats['especial2'])
				x += 1

			worksheet.write(x, 0, line.name if line.name else '', formatLeft)
			worksheet.write(x, 1, line.l10n_latam_identification_type_id.name if line.l10n_latam_identification_type_id else '', formatCenter)
			worksheet.write(x, 2, line.vat if line.vat else '', formatCenter)
			worksheet.write(x, 3, dict(line._fields['parents'].selection).get(line.parents) if line.parents else '', dateformat)
			worksheet.write(x, 4, line.birthday if line.birthday else '', dateformat)
			worksheet.write(x, 5, str(line.age) if line.age else '0', formatCenter)
			worksheet.write(x, 6, 'Si' if line.study else 'No', dateformat)

			x += 1

		widths = [30, 14, 15, 16, 14, 12, 20]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()
		f = open(directory + 'Reporte_derechohabientes.xlsx', 'rb')
		return self.env['popup.it'].get_file('Reporte Derechohabientes.xlsx', base64.encodebytes(b''.join(f.readlines())))