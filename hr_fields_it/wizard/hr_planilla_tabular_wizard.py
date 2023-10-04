# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
import base64
from datetime import *
from math import modf
from string import ascii_lowercase
import itertools

class HrPlanillaTabularSalaryWizard(models.TransientModel):
	_name = 'hr.planilla.tabular.salary.wizard'
	_description = 'Hr Planilla Tabular Salary Wizard'

	name = fields.Char()
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	payslip_run_id = fields.Many2one('hr.payslip.run', string='Periodo')
	employees_ids = fields.Many2many('hr.employee','hr_planilla_salary_employee_rel','payslip_multi_id','employee_id',string=u'Empleados')
	allemployees = fields.Boolean('Todos los Empleados',default=True)
	type_show =  fields.Selection([('pantalla','Pantalla'),('excel','Excel')],default='pantalla',string=u'Mostrar en', required=True)

	@api.model
	def default_get(self, fields):
		res = super(HrPlanillaTabularSalaryWizard, self).default_get(fields)
		payslip_run_id = res.get('payslip_run_id')
		res.update({'payslip_run_id': payslip_run_id})
		return res

	@api.onchange('allemployees')
	def onchange_allemployees(self):
		if self.allemployees==False:
			employee_ids = []
			for employe in self.payslip_run_id.slip_ids:
				employee_ids.append(employe.employee_id.id)
			# print("employee_ids",employee_ids)
			domain = {"employees_ids": [("id", "in", employee_ids)]}
			return {"domain": domain}

	def _get_sql(self,option):
		sql_employees = "and he.id in (%s) " % (','.join(str(i) for i in self.employees_ids.ids)) if option == 1 else ""
		sql_payslips = "and hp.id in (%s)" % (','.join(str(i) for i in self.payslip_run_id.slip_ids.ids))

		sql = """SELECT row_number() OVER () AS id, T.* FROM (
            select
			he.id as employee_id,
			he.identification_id,
			hsr.id as salary_rule_id,
			hsr.code,
			sum(hpl.total) as amount,
			hsr.sequence
			from hr_payslip hp
			inner join hr_payslip_line hpl on hpl.slip_id = hp.id
			inner join hr_salary_rule hsr on hsr.id = hpl.salary_rule_id
			inner join hr_employee he on he.id = hp.employee_id
			where hsr.appears_on_payslip = true
			and hsr.active = true
			and hsr.company_id = %d
			and hpl.total <> 0
			%s %s
			group by he.identification_id, he.id, hsr.id, hsr.code, hsr.sequence
			order by he.identification_id, hsr.sequence
			)T
			"""%(self.company_id.id,
				 sql_payslips,
				 sql_employees)
		return sql

	def get_all(self):
		# self.domain_dates()
		self.env.cr.execute("""
				CREATE OR REPLACE view hr_planilla_tabular as (""" + self._get_sql(0) + """)""")

		if self.type_show == 'pantalla':
			return {
				'name': 'Reporte Planilla Tabular',
				'type': 'ir.actions.act_window',
				'res_model': 'hr.planilla.tabular',
				'view_mode': 'pivot',
				'view_type': 'pivot',
			}
		option=0
		if self.type_show == 'excel':
			return self.get_excel(option)

	def get_journals(self):
		# self.domain_dates()
		if self.allemployees == False:
			self.env.cr.execute("""
					CREATE OR REPLACE view hr_planilla_tabular as (""" + self._get_sql(1) + """)""")

			if self.type_show == 'pantalla':
				return {
					'name': 'Reporte Planilla Tabular',
					'type': 'ir.actions.act_window',
					'res_model': 'hr.planilla.tabular',
					'view_mode': 'pivot',
					'view_type': 'pivot',
					'views': [(False, 'pivot')],
				}
			option=1
			if self.type_show == 'excel':
				return self.get_excel(option)
		else:
			raise UserError('Debe escoger al menos un Empleado.')

	def _get_tab_payroll_sql(self,option):
		sql_employees = "and he.id in (%s) " % (','.join(str(i) for i in self.employees_ids.ids)) if option == 1 else ""
		struct_id = self.payslip_run_id.slip_ids[0].struct_id.id
		sql = """
			select
			he.id as employee_id,
			he.identification_id,
			hc.date_start,
			hm.name as membership,
			had.name as distribution,
			hsr.code,
			hsr.name as name_salary,
			sum(hpl.total)
			from hr_payslip hp
			inner join hr_payslip_line hpl on hpl.slip_id = hp.id
			inner join hr_salary_rule hsr on hsr.id = hpl.salary_rule_id
			inner join hr_employee he on he.id = hp.employee_id
			inner join hr_contract hc on hc.id = hp.contract_id
			left join hr_membership hm on hm.id = hc.membership_id
			left join hr_analytic_distribution had on had.id = hc.distribution_id
			where hp.id in ({ids})
			and hsr.appears_on_payslip = true
			and hsr.active = true
			and hsr.company_id = {company}
			and hsr.struct_id = {struct_id}
			{sql_employees}
			group by he.identification_id, he.id, hc.date_start, hsr.code, hsr.name, hm.name, had.name, hsr.sequence
			order by he.identification_id, hsr.sequence
		""".format(
				ids = ','.join(list(map(str, self.payslip_run_id.slip_ids.ids))),
				company = self.company_id.id,
				struct_id = struct_id,
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

		workbook = Workbook(directory + 'Planilla_Tabular.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		worksheet = workbook.add_worksheet("Planilla Tabular")
		worksheet.set_tab_color('blue')

		worksheet.merge_range(0, 0, 0, 7, "Empresa: %s" % self.company_id.partner_id.name or '', formats['especial2'])
		worksheet.merge_range(1, 0, 1, 7, "RUC: %s" % self.company_id.partner_id.vat or '', formats['especial2'])
		worksheet.merge_range(2, 0, 2, 7, "Direccion: %s" % self.company_id.partner_id.street or '', formats['especial2'])
		worksheet.merge_range(4, 1, 4, 8, "*** PLANILLA DE SUELDOS Y SALARIOS %s ***"  % self.payslip_run_id.name.name or '', formats['especial5'])

		self._cr.execute(self._get_tab_payroll_sql(option))
		data = self._cr.dictfetchall()
		x, y = 6, 6
		limit = len(data[0] if data else 0)
		# struct_id = self.payslip_run_id.slip_ids[0].struct_id.id
		# SalaryRules = self.env['hr.salary.rule'].search([('appears_on_payslip', '=', True), ('struct_id', '=', struct_id)], order='sequence')
		# names = SalaryRules.mapped('name')
		# codes = SalaryRules.mapped('code')
		names = []
		codes = []
		for elem in data:
			if elem['code'] in codes:
				continue
			else:
				names.append(elem['name_salary'])
				codes.append(elem['code'])
		# names = SalaryRules.mapped('name')
		# print("names", names)
		# codes = SalaryRules.mapped('code')
		# print("codes", codes)
		size = len(codes)

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

		formatLeft = workbook.add_format(
			{'num_format': '0.00', 'font_name': 'Arial', 'align': 'left', 'font_size': 8})
		numberdos = workbook.add_format(
			{'num_format': '0.00', 'font_name': 'Arial', 'align': 'right'})
		numberdos.set_font_size(8)
		styleFooterSum = workbook.add_format(
			{'bold': True, 'num_format': '0.00', 'font_name': 'Arial', 'align': 'right', 'font_size': 9, 'top': 1, 'bottom': 2})
		styleFooterSum.set_bottom(6)

		worksheet.write(x, 0, 'NRO IDENTIFICACION', boldbord)
		worksheet.write(x, 1, 'NOMBRE', boldbord)
		worksheet.write(x, 2, 'TITULO DE TRABAJO', boldbord)
		worksheet.write(x, 3, 'INICIO DE CONTRATO', boldbord)
		worksheet.write(x, 4, 'AFILIACION', boldbord)
		worksheet.write(x, 5, 'DISTRIBUCION ANALITICA', boldbord)

		for name in names:
			worksheet.write(x, y, name, boldbord)
			y += 1
		x += 1
		table = []
		row = []
		aux_id, limit = '', len(data)
		for c, line in enumerate(data, 1):
			if aux_id != line['employee_id']:
				if len(row) > 0:
					table.append(row)
					x += 1
				row = []
				employee = self.env['hr.employee'].browse(line['employee_id'])
				worksheet.write(x, 0, line['identification_id'] if line['identification_id'] else '', formatLeft)
				worksheet.write(x, 1, employee.name if employee.name else '', formatLeft)
				worksheet.write(x, 2, employee.job_title if employee.job_title else '', formatLeft)
				worksheet.write(x, 3, line['date_start'] if line['date_start'] else '', dateformat)
				worksheet.write(x, 4, line['membership'] if line['membership'] else '', formatLeft)
				worksheet.write(x, 5, line['distribution'] if line['distribution'] else '', formatLeft)
				worksheet.write(x, 6, line['sum'] if line['sum'] else 0.0, numberdos)
				row.append(line['sum'])
				y = 6
				aux_id = line['employee_id']
			else:
				y += 1
				worksheet.write(x, y, line['sum'] if line['sum'] else 0.0, numberdos)
				aux_id = line['employee_id']
				row.append(line['sum'])
				if c == limit:
					table.append(row)
					x += 1

		zipped_table = zip(*table)
		y = 6
		for row in zipped_table:
			worksheet.write(x+1, y, sum(list(row)), styleFooterSum)
			y += 1
		widths = [12, 30, 22, 12, 16, 15] + size * [13]
		worksheet = self.resize_cells(worksheet,widths)
		workbook.close()
		f = open(directory + 'Planilla_Tabular.xlsx', 'rb')
		return self.env['popup.it'].get_file('Planilla %s.xlsx' % self.payslip_run_id.name.name, base64.encodebytes(b''.join(f.readlines())))


	def resize_cells(self,worksheet,widths):
		CELLS=[]
		for s in itertools.islice(self.iter_all_strings(), 100):
			CELLS.append(s.upper())
		for c,width in enumerate(widths):
			worksheet.set_column('%s:%s' % (CELLS[c],CELLS[c]), width)
		return worksheet

	def iter_all_strings(self):
		size = 1
		while True:
			for s in itertools.product(ascii_lowercase, repeat=size):
				yield "".join(s)
			size +=1