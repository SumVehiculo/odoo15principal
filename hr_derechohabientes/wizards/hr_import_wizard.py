# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError
import base64
import subprocess

def install(package):
	subprocess.check_call([sys.executable, "-m", "pip", "install", package])
try:
	from xlrd import *
except:
	install('xlrd')

class HrImportWizard(models.TransientModel):
	_inherit = 'hr.import.wizard'

	option = fields.Selection([('employee', 'Empleados'),
							   ('contract', 'Contratos'),
							   ('derechohabientes', 'Derechohabientes')], default='employee', string='Opcion')

	def get_template(self):
		if self.option == 'employee':
			return self.get_employee_template()
		elif self.option == 'contract':
			return self.get_contract_template()
		else:
			return self.get_derechohabiente_template()

	def import_template(self):
		if self.option == 'employee':
			return self.import_employee_template()
		elif self.option == 'contract':
			return self.import_contract_template()
		else:
			return self.import_derechohabiente_template()


	def get_derechohabiente_template(self):
		import io
		from xlsxwriter.workbook import Workbook
		Employee = self.env['hr.derechohabientes']
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		ReportBase = self.env['report.base']
		if not MainParameter.dir_create_file:
			raise UserError('Falta configurar un directorio de descargas en Parametros Principales')
		route = MainParameter.dir_create_file
		workbook = Workbook(route + 'Plantilla Derechohabientes.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		worksheet = workbook.add_worksheet('DERECHOHABIENTES')
		worksheet.set_tab_color('blue')
		HEADERS = ['NOMBRES Y APELLIDOS', 'TIPO DE DOCUMENTO', 'NUMERO DOCUMENTO', 'PARENTESCO', 'FECHA NACIMIENTO',
				'CURSANDO ESTUDIOS','DNI EMPLEADO']
		worksheet = ReportBase.get_headers(worksheet, HEADERS, 0, 0, formats['boldbord'])
		worksheet.write(1, 0, 'MARIVEL ROCIO BUSTAMANTE ARMEJO', formats['especial1'])
		worksheet.write(1, 1, 'DNI', formats['especial1'])
		worksheet.write(1, 2, '42123456', formats['especial1'])
		worksheet.write(1, 3, 'Hijo/a', formats['especial1'])
		worksheet.write(1, 4, '', formats['reverse_dateformat'])
		worksheet.write(1, 5, 'Si', formats['especial1'])
		worksheet.write(1, 6, '75123456', formats['especial1'])

		# print(self.env['hr.worker.type'].search([]).mapped('name'), self.env['hr.payroll.structure.type'].search([]).mapped('name'))
		worksheet.data_validation('B2', {'validate': 'list',
										 'source': self.env['l10n_latam.identification.type'].search([]).mapped('name')})
		worksheet.data_validation('D2', {'validate': 'list',
										 'source': list(dict(Employee._fields['parents'].selection).values())})
		worksheet.data_validation('F2', {'validate': 'list',
										 'source': list(['Si','No'])})
										 
		widths = [38] + 29 * [18]
		worksheet = ReportBase.resize_cells(worksheet, widths)

		workbook.close()

		f = open(route + 'Plantilla Derechohabientes.xlsx', 'rb')
		return self.env['popup.it'].get_file('Plantilla Derechohabientes.xlsx', base64.encodebytes(b''.join(f.readlines())))

	def verify_derechohabiente_sheet(self, employee_sheet, datemode):
		log = ''
		Employee = self.env['hr.derechohabientes']
		for i in range(1, employee_sheet.nrows):
			j = i + 1
			if not self.env['hr.employee'].search([('identification_id', '=', self.parse_xls_float(employee_sheet.cell_value(i, 6)))], limit=1):
				log += 'El Empleado de la linea %d de la hoja DERECHOHABIENTES no existe en el sistema\n' % j
			if not employee_sheet.cell_value(i, 0):
				log += 'Faltan Nombres y Apellidos en la linea %d de la hoja DERECHOHABIENTES, estos son campos obligatorios\n' % j
			if not self.env['l10n_latam.identification.type'].search([('name', '=', employee_sheet.cell_value(i, 1))], limit=1):
				log += 'El Tipo de Documento de la linea %d de la hoja DERECHOHABIENTES no existe en el sistema\n' % j
			if not employee_sheet.cell_value(i, 2):
				log += 'Falta el DNI en la linea %d de la hoja DERECHOHABIENTES, estos son campos obligatorios\n' % j
			if employee_sheet.cell_value(i, 5) not in list(['Si','No']):
				log += 'El Nivel de estudio de la linea %d de la hoja DERECHOHABIENTES no existe en el sistema\n' % j
			try:
				if employee_sheet.cell_value(i, 4):
					xldate.xldate_as_datetime(employee_sheet.cell_value(i, 4), datemode)
			except:
				log += 'La Fecha de Nacimiento de la linea %d de la hoja DERECHOHABIENTES tiene un problema.\n' % j
		if log:
			raise UserError('Se han detectado los siguientes errores:\n' + log)

	def import_derechohabiente_template(self):
		if not self.file:
			raise UserError('Es necesario especificar un archivo de importacion para este proceso')
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		route = MainParameter.dir_create_file + 'Import_Derechohabiente_Template.xlsx'
		Company = self.env.company
		Employee = self.env['hr.derechohabientes']
		tmp = open(route, 'wb+')
		tmp.write(base64.b64decode(self.file))
		tmp.close()
		wb = open_workbook(route)

		####DERECHOHABIENTES SHEET####
		employee_sheet = wb.sheet_by_index(0)
		self.verify_derechohabiente_sheet(employee_sheet, wb.datemode)

		
		parents = dict(Employee._fields['parents'].selection)
		if employee_sheet.ncols != 7:
			raise UserError('La hoja de DERECHOHABIENTES debe tener solo 7 columnas.')
		for i in range(1, employee_sheet.nrows):

			self.env['hr.derechohabientes'].create({
											'employee_id': self.env['hr.employee'].search([('identification_id', '=', self.parse_xls_float(employee_sheet.cell_value(i, 6)))], limit=1).id,
											'name': employee_sheet.cell_value(i, 0),
											'l10n_latam_identification_type_id': self.env['l10n_latam.identification.type'].search([('name', '=', employee_sheet.cell_value(i, 1))], limit=1).id,
											'vat': self.parse_xls_float(employee_sheet.cell_value(i, 2)),
											'parents': [key for key, val in parents.items() if val == employee_sheet.cell_value(i, 3)][0],
											'birthday': xldate.xldate_as_datetime(employee_sheet.cell_value(i, 4), wb.datemode) if employee_sheet.cell_value(i, 4) else None,
											'study': True if 'Si'  == employee_sheet.cell_value(i, 5) else False,
										})
		return self.env['popup.it'].get_message('Se importaron todos los familiares satisfactoriamente')