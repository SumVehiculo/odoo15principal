# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError
import base64
from datetime import *
import subprocess

def install(package):
	subprocess.check_call([sys.executable, "-m", "pip", "install", package])

try:
	from xlrd import *
except:
	install('xlrd')

class HrImportWdWizard(models.TransientModel):
	_name = 'hr.import.wd.wizard'
	_description = 'Import WD Wizard'

	name = fields.Char()
	file = fields.Binary(string='Archivo de Exportacion')
	option = fields.Selection([('wd', 'Worked Days'), ('input', 'Input')], default='wd', string='Opcion')

	def parse_xls_float(self, cell_value):
		if type(cell_value) is float:
			return str(int(cell_value))
		else:
			return cell_value

	def get_template(self):
		if self.option == 'wd':
			return self.get_wd_template()
		else:
			return self.get_input_template()

	def import_template(self):
		if self.option == 'wd':
			return self.import_wd_template()
		else:
			return self.import_input_template()

	def get_wd_template(self):
		import io
		from xlsxwriter.workbook import Workbook
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		ReportBase = self.env['report.base']
		if not MainParameter.dir_create_file:
			raise UserError('Falta configurar un directorio de descargas en Parametros Principales')
		route = MainParameter.dir_create_file
		workbook = Workbook(route + 'Plantilla Worked Days.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		worksheet = workbook.add_worksheet('WD')
		worksheet.set_tab_color('blue')
		HEADERS = ['EMPLEADO', 'CODIGO', 'NRO DIAS', 'NRO HORAS']
		worksheet = ReportBase.get_headers(worksheet, HEADERS, 0, 0, formats['boldbord'])
		worksheet.write(1, 0, '45653672', formats['especial1'])
		worksheet.write(1, 1, 'DLAB', formats['especial1'])
		worksheet.write(1, 2, 0, formats['especial1'])
		worksheet.write(1, 3, 0.0, formats['especial1'])
		# worksheet.write(1, 3, '0:00', formats['hourformat'])

		worksheet.data_validation('A2', {'validate': 'list',
										 'source': self.env['hr.employee'].search([]).mapped('identification_id')})
		worksheet.data_validation('B2', {'validate': 'list',
										 'source': self.env['hr.payslip.worked_days.type'].search([]).mapped('code')})
		widths = 4 * [18]
		worksheet = ReportBase.resize_cells(worksheet, widths)

		workbook.close()

		f = open(route + 'Plantilla Worked Days.xlsx', 'rb')
		return self.env['popup.it'].get_file('Plantilla Worked Days.xlsx', base64.encodebytes(b''.join(f.readlines())))

	def get_input_template(self):
		import io
		from xlsxwriter.workbook import Workbook
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		ReportBase = self.env['report.base']
		if not MainParameter.dir_create_file:
			raise UserError('Falta configurar un directorio de descargas en Parametros Principales')
		route = MainParameter.dir_create_file
		workbook = Workbook(route + 'Plantilla Inputs.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		worksheet = workbook.add_worksheet('INPUTS')
		worksheet.set_tab_color('blue')
		HEADERS = ['EMPLEADO', 'CODIGO', 'MONTO']
		worksheet = ReportBase.get_headers(worksheet, HEADERS, 0, 0, formats['boldbord'])
		worksheet.write(1, 0, '45653672', formats['especial1'])
		worksheet.write(1, 1, 'GRA', formats['especial1'])
		worksheet.write(1, 2, 0.0, formats['numberdos'])

		worksheet.data_validation('A2', {'validate': 'list',
										 'source': self.env['hr.employee'].search([]).mapped('identification_id')})
		worksheet.data_validation('B2', {'validate': 'list',
										 'source': self.env['hr.payslip.input.type'].search([]).mapped('code')})
		widths = 3 * [18]
		worksheet = ReportBase.resize_cells(worksheet, widths)

		workbook.close()

		f = open(route + 'Plantilla Inputs.xlsx', 'rb')
		return self.env['popup.it'].get_file('Plantilla Inputs.xlsx', base64.encodebytes(b''.join(f.readlines())))


	def import_wd_template(self):
		if not self.file:
			raise UserError('Es necesario adjuntar un archivo para la importacion')
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		route = MainParameter.dir_create_file + 'Import_WD.xlsx'
		tmp = open(route, 'wb+')
		tmp.write(base64.b64decode(self.file))
		tmp.close()
		wb = open_workbook(route)
		sheet = wb.sheet_by_index(0)
		if sheet.ncols != 4:
			raise UserError('El archivo de importacion debe tener 4 columnas con la siguiente forma: \n \t EMPLEADO | CODIGO | NRO_DIAS | NRO_HORAS')
		Payslips = self.env['hr.payslip'].browse(self._context.get('payslip_ids'))
		for i in range(1, sheet.nrows):
			Payslip = Payslips.filtered(lambda p: p.employee_id.identification_id == self.parse_xls_float(sheet.cell_value(i, 0)))
			if Payslip:
				WD = Payslip.worked_days_line_ids.filtered(lambda wd: wd.code == sheet.cell_value(i, 1))
				if WD:
					WD.number_of_days = sheet.cell_value(i, 2)
					# hour = sheet.cell_value(i, 3)
					# print("dias",sheet.cell_value(i, 2))
					# print("horas",hour)
					# if hour < 1:
					# 	hour = int(hour * 24 * 3600)
					# 	hour = time(hour//3600, (hour % 3600)//60, hour % 60)
					# 	WD.number_of_hours = hour.hour + hour.minute/60
					# else:
					WD.number_of_hours = sheet.cell_value(i, 3)

		return self.env['popup.it'].get_message('Se importaron todos los worked days satisfactoriamente')

	def import_input_template(self):
		if not self.file:
			raise UserError('Es necesario adjuntar un archivo para la importacion')
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		route = MainParameter.dir_create_file + 'Import_Inputs.xlsx'
		tmp = open(route, 'wb+')
		tmp.write(base64.b64decode(self.file))
		tmp.close()
		wb = open_workbook(route)
		sheet = wb.sheet_by_index(0)
		if sheet.ncols != 3:
			raise UserError('El archivo de importacion debe tener 3 columnas con la siguiente forma: \n \t EMPLEADO | CODIGO | MONTO')
		Payslips = self.env['hr.payslip'].browse(self._context.get('payslip_ids'))
		for i in range(1, sheet.nrows):
			Payslip = Payslips.filtered(lambda p: p.employee_id.identification_id == self.parse_xls_float(sheet.cell_value(i, 0)))
			if Payslip:
				INPUT = Payslip.input_line_ids.filtered(lambda input: input.code == sheet.cell_value(i, 1))
				if INPUT:
					INPUT.amount = sheet.cell_value(i, 2)

		return self.env['popup.it'].get_message('Se importaron todos los inputs satisfactoriamente')