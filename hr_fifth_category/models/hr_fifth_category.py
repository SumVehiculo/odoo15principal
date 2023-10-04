# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError
from datetime import *
import base64

class HrFifthCategory(models.Model):
	_name = 'hr.fifth.category'
	_description = 'Fifth Category'

	name = fields.Char(compute='_get_name')
	payslip_run_id = fields.Many2one('hr.payslip.run', string='Periodo', required=True, states={'exported': [('readonly', True)]})
	company_id = fields.Many2one('res.company', string='Compañia', default=lambda self: self.env.company.id, required=True, states={'exported': [('readonly', True)]})
	line_ids = fields.One2many('hr.fifth.category.line', 'fifth_category_id', string='Afectos a Quinta', states={'exported': [('readonly', True)]})
	line_excluidos_ids = fields.One2many('hr.fifth.category.line.excluidos', 'fifth_category_id', string='Excluidos de Quinta', states={'exported': [('readonly', True)]})
	state = fields.Selection([('draft', 'Borrador'),('verify', 'En Proceso'),('exported', 'Exportado')], default='draft', string='Estado')

	@api.depends('payslip_run_id')
	def _get_name(self):
		for record in self:
			if record.payslip_run_id:
				record.name = 'Quinta {0}'.format(record.payslip_run_id.name.name)

	def turn_draft(self):
		self.line_ids.unlink()
		self.line_excluidos_ids.unlink()
		self.state = 'draft'

	def turn_verify(self):
		self.state = 'verify'

	def export_fifth(self):
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		MainParameter.check_fifth_values()
		for line in self.line_ids:
			fifth_inp = line.slip_id.input_line_ids.filtered(lambda inp: inp.input_type_id == MainParameter.fifth_category_input_id)
			fifth_inp.amount = line.monthly_ret
		self.state = 'exported'
		return self.env['popup.it'].get_message('Se exporto exitosamente')

	def generate_fifth(self):
		for slip in self.payslip_run_id.slip_ids:
			self.env['hr.fifth.category.line'].create({
													'fifth_category_id': self.id,
													'slip_id': slip.id
												})
		self.line_ids.compute_fifth_line()
		self.state = 'verify'
		return self.env['popup.it'].get_message('Se genero la Quinta de manera Correcta')
	
	def recompute_fifth(self):
		self.line_ids.compute_fifth_line()

	def get_employees_excluidos(self):
		wizard = self.env['hr.employee.excluidos.wizard'].create({
			'fifth_category_id': self.id,
			'company_id':self.company_id.id
		})
		module = __name__.split('addons.')[1].split('.')[0]
		view = self.env.ref('%s.view_hr_employee_excluidos_wizard' % module)
		return {
			'name':u'Seleccionar Empleados',
			'res_id':wizard.id,
			'view_mode': 'form',
			'res_model': 'hr.employee.excluidos.wizard',
			'view_id': view.id,
			'context': self.env.context,
			'target': 'new',
			'type': 'ir.actions.act_window',
		}

	def get_excel_fifth(self):
		import io
		from xlsxwriter.workbook import Workbook
		Employee = self.env['hr.employee']
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		ReportBase = self.env['report.base']
		if not MainParameter.dir_create_file:
			raise UserError('Falta configurar un directorio de descargas en Parametros Principales')
		route = MainParameter.dir_create_file
		workbook = Workbook(route + 'Quinta.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		worksheet = workbook.add_worksheet('QUINTA %s' % self.payslip_run_id.name.name)
		worksheet.set_tab_color('blue')
		HEADERS = ['EMPLEADO','N° IDENTIFICACION', 'REMUNERACION MENSUAL', 'REM. PROY. SEGUN CONTRATO', 'REMUNERACION PROYECTADA', 'GRATIFICACION JULIO', 'GRATIFICACION DICIEMBRE',
				'REM. PROY. OTROS EMPLEADORES', 'REMUNERACIONES ANTERIORES', 'TOTAL PROYECTADO', 'DEDUCCION 7UIT', 'RENTA NETA', 'IMPUESTO PROYECTADO',
				'RETENCION MESES ANTERIORES', 'RETENCION OTROS EMPLEADORES', 'RETENCION ANUAL', 'RENTA MENSUAL', 'REMUNERACION EXTRAORDINARIA', 'TOTAL RENTA NETA',
				'RETENCION EXTRAORDINARIA', 'RETENCION MENSUAL']
		worksheet = ReportBase.get_headers(worksheet, HEADERS, 0, 0, formats['boldbord'])
		x = 1

		totals = [0] * 19
		limiter = 2

		for line in self.line_ids:
			worksheet.write(x, 0, line.employee_id.name, formats['especial1'])
			worksheet.write(x, 1, line.employee_id.identification_id, formats['especial1'])
			worksheet.write(x, 2, line.monthly_rem, formats['numberdos'])
			worksheet.write(x, 3, line.contrac_proy_rem, formats['numberdos'])
			worksheet.write(x, 4, line.proy_rem, formats['numberdos'])
			worksheet.write(x, 5, line.grat_july, formats['numberdos'])
			worksheet.write(x, 6, line.grat_december, formats['numberdos'])
			worksheet.write(x, 7, line.other_emp_proy_rem, formats['numberdos'])
			worksheet.write(x, 8, line.past_rem, formats['numberdos'])
			worksheet.write(x, 9, line.total_proy, formats['numberdos'])
			worksheet.write(x, 10, line.seven_uit, formats['numberdos'])
			worksheet.write(x, 11, line.net_rent, formats['numberdos'])
			worksheet.write(x, 12, line.tax_proy, formats['numberdos'])
			worksheet.write(x, 13, line.past_months_ret, formats['numberdos'])
			worksheet.write(x, 14, line.other_emp_ret, formats['numberdos'])
			worksheet.write(x, 15, line.annual_ret, formats['numberdos'])
			worksheet.write(x, 16, line.monthly_rent, formats['numberdos'])
			worksheet.write(x, 17, line.ext_rem, formats['numberdos'])
			worksheet.write(x, 18, line.total_net_rent, formats['numberdos'])
			worksheet.write(x, 19, line.ext_ret, formats['numberdos'])
			worksheet.write(x, 20, line.monthly_ret, formats['numberdos'])

			totals[0] += line.monthly_rem
			totals[1] += line.contrac_proy_rem
			totals[2] += line.proy_rem
			totals[3] += line.grat_july
			totals[4] += line.grat_december
			totals[5] += line.other_emp_proy_rem
			totals[6] += line.past_rem
			totals[7] += line.total_proy
			totals[8] += line.seven_uit
			totals[9] += line.net_rent
			totals[10] += line.tax_proy
			totals[11] += line.past_months_ret
			totals[12] += line.other_emp_ret
			totals[13] += line.annual_ret
			totals[14] += line.monthly_rent
			totals[15] += line.ext_rem
			totals[16] += line.total_net_rent
			totals[17] += line.ext_ret
			totals[18] += line.monthly_ret

			x += 1
		x += 1
		for total in totals:
			worksheet.write(x, limiter, total, formats['numbertotal'])
			limiter += 1

		widths = [40] + 20 * [20]
		worksheet = ReportBase.resize_cells(worksheet, widths)

		workbook.close()

		f = open(route + 'Quinta.xlsx', 'rb')
		return self.env['popup.it'].get_file('Quinta %s.xlsx' % self.payslip_run_id.name.name, base64.encodebytes(b''.join(f.readlines())))

class HrFifthCategoryLine(models.Model):
	_name = 'hr.fifth.category.line'
	_description = 'Fifth Category Line'

	fifth_category_id = fields.Many2one('hr.fifth.category', ondelete='cascade')
	slip_id = fields.Many2one('hr.payslip', string='Nomina', required=True)
	employee_id = fields.Many2one(related='slip_id.employee_id', string='Empleado', required=True)
	identification_id = fields.Char(related='slip_id.employee_id.identification_id', string='N° Identificacion')
	monthly_rem = fields.Float(string='Remuneracion Mensual')
	contrac_proy_rem = fields.Float(string='Rem. Proy. Segun Contrato', help='Remuneracion Proyectada Segun Contrato')
	proy_rem = fields.Float(string='Remuneracion Proyectada')
	grat_july = fields.Float(string='Gratificacion Julio')
	grat_december = fields.Float(string='Gratificacion Diciembre')
	other_emp_proy_rem = fields.Float(string='Rem. Proy. Otros Empleadores')
	past_rem = fields.Float(string='Remuneraciones Anteriores')
	total_proy = fields.Float(string='Total Proyectado')
	seven_uit = fields.Float(string='Deduccion 7 UIT')
	net_rent = fields.Float(string='Renta Neta')
	tax_proy = fields.Float(string='Impuesto Proyectado')
	past_months_ret = fields.Float(string='Retencion Meses Anteriores')
	other_emp_ret = fields.Float(string='Retencion Otros Empleadores')
	annual_ret = fields.Float(string='Retencion Anual')
	monthly_rent = fields.Float(string='Renta Mensual')
	ext_rem = fields.Float(string='Remuneracion Extraordinaria')
	total_net_rent = fields.Float(string='Total Renta Neta')
	ext_ret = fields.Float(string='Retencion Extraordinaria')
	monthly_ret = fields.Float(string='Retencion Mensual')
	real_other_emp_rem = fields.Float(string='Rem. Real Otros Empleadores')

	def get_past_rem(self, slip, date_from):
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		MainParameter.check_fifth_values()
		sql = """
select T.employee_id,
       sum(T.total) as total
from (select hpl.employee_id,
             hpl.total
      from hr_payslip_line hpl
               inner join hr_payslip hp on hp.id = hpl.slip_id
      where hpl.date_from >= '{0}'
        and hpl.date_from < '{1}'
        and hpl.employee_id = {2}
        and hpl.salary_rule_id in ({3},{4})
        and hp.payslip_run_id is not null)T
group by T.employee_id
				""".format(date_from, slip.date_from, slip.employee_id.id,
						   MainParameter.fifth_afect_sr_id.id,
						   MainParameter.fifth_extr_sr_id.id)
		self._cr.execute(sql)
		past_lines = self._cr.dictfetchall()
		rem_ant = past_lines[0]['total'] if past_lines else 0
		# print("rem_ant",rem_ant)
		# rem_ant_ext = sum(past_lines.filtered(lambda line: line.salary_rule_id == MainParameter.fifth_extr_sr_id).mapped('total'))
		other_past_rem = self.env['hr.fifth.category.line'].search([
			('slip_id.date_from', '>=', date_from),
			('slip_id.date_from', '<', slip.date_from),
			('employee_id', '=', slip.employee_id.id)
		])
		return rem_ant + sum(other_past_rem.mapped('other_emp_proy_rem'))

	def get_tax_proy(self, net_rent, lines):
		tax_proy = tax = 0
		for line in lines:
			if net_rent > line.limit and line.limit > 0:
				tax_proy += (line.limit - tax) * line.rate * 0.01
				tax += line.limit - tax
			else:
				tax_proy += (net_rent - tax) * line.rate * 0.01
				break
		return tax_proy

	def get_past_months_ret(self, slip, date_from):
		other_past_ret = self.env['hr.fifth.category.line'].search([
			('slip_id.date_from', '>=', date_from),
			('slip_id.date_from', '<', slip.date_from),
			('employee_id', '=', slip.employee_id.id)
		])

		sr_quinta_id = self.env['hr.salary.rule'].search([('company_id', '=', self.env.company.id),('code', '=', 'QUINTA')], limit=1)
		if slip.date_from.month in (1,2,3):
			return 0 + sum(other_past_ret.mapped('other_emp_ret'))
		elif slip.date_from.month in (4, 5, 8, 9, 12):
			sql = """
			select T.employee_id,
				   sum(T.total) as total
			from (select hpl.employee_id,
						 hpl.total
				  from hr_payslip_line hpl
						   inner join hr_payslip hp on hp.id = hpl.slip_id
				  where hpl.date_from >= '{0}'
					and hpl.date_from < '{1}'
					and hpl.employee_id = {2}
					and hpl.salary_rule_id = {3}
					and hp.payslip_run_id is not null)T
			group by T.employee_id
				""".format(date_from, slip.date_from, slip.employee_id.id, sr_quinta_id.id)
			self._cr.execute(sql)
			past_lines = self._cr.dictfetchall()

		elif slip.date_from.month in (6, 7):
			sql = """
			select T.employee_id,
				   sum(T.total) as total
			from (select hpl.employee_id,
						 hpl.total
				  from hr_payslip_line hpl
						   inner join hr_payslip hp on hp.id = hpl.slip_id
				  where hpl.date_from >= '{0}'
					and hpl.date_from < '{1}'
					and hpl.employee_id = {2}
					and hpl.salary_rule_id = {3}
					and hp.payslip_run_id is not null)T
			group by T.employee_id
				""".format(date_from, date(date_from.year, 4, 30), slip.employee_id.id, sr_quinta_id.id)
			self._cr.execute(sql)
			past_lines = self._cr.dictfetchall()

		elif slip.date_from.month in (10, 11):
			sql = """
			select T.employee_id,
				   sum(T.total) as total
			from (select hpl.employee_id,
						 hpl.total
				  from hr_payslip_line hpl
						   inner join hr_payslip hp on hp.id = hpl.slip_id
				  where hpl.date_from >= '{0}'
					and hpl.date_from < '{1}'
					and hpl.employee_id = {2}
					and hpl.salary_rule_id = {3}
					and hp.payslip_run_id is not null)T
			group by T.employee_id
				""".format(date_from, date(date_from.year, 8, 31), slip.employee_id.id, sr_quinta_id.id)
			self._cr.execute(sql)
			past_lines = self._cr.dictfetchall()

		# ret_quinta = sum(past_lines.filtered(lambda line: line.salary_rule_id.code == 'QUINTA').mapped('total'))
		ret_ant = past_lines[0]['total'] if past_lines else 0
		# print("ret_quinta",ret_quinta)
		return ret_ant + sum(other_past_ret.mapped('other_emp_ret'))

	def get_month_equivalence_proy(self, month):
		return 12 - month

	def get_month_equivalence_rent(self, month):
		month_equivalence = [12, 12, 12, 9, 8, 8, 8, 5, 4, 4, 4, 1]
		return month_equivalence[month - 1]

	def compute_fifth_line(self):
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		MainParameter.check_fifth_values()
		ReportBase = self.env['report.base']
		#Esta línea se agregó porque el usuario solía descartar una línea después del cálculo, por lo que esto crea
		#una línea sin encabezado y que causan errores de cálculo
		self.env['hr.fifth.category.line'].search([('fifth_category_id', '=', None), ('id', 'not in', self.ids)]).unlink()

		for record in self:
			Slip = record.slip_id
			month = Slip.date_from.month
			proy_month = self.get_month_equivalence_proy(month)
			rent_month = self.get_month_equivalence_rent(month)
			FiscalYear = self.env['account.fiscal.year'].search([('date_from', '<=', Slip.date_from), ('date_to', '>=', Slip.date_from)])
			uit = FiscalYear.uit
			Employee, Contract = Slip.employee_id, Slip.contract_id
			if month >= 7:
				grat_july = self.env['hr.gratification.line'].search([
																('gratification_id.type', '=', '07'), 
																('employee_id', '=', Employee.id),
																('gratification_id.fiscal_year_id', '=', FiscalYear.id)
															])
			if month == 12:
				grat_december = self.env['hr.gratification.line'].search([
																('gratification_id.type', '=', '12'), 
																('employee_id', '=', Employee.id),
																('gratification_id.fiscal_year_id', '=', FiscalYear.id)
															])

			record.monthly_rem = Slip.line_ids.filtered(lambda line: line.salary_rule_id == MainParameter.fifth_afect_sr_id).total

			if Contract.situation_id.code == '0':
				grat_july_proy = 0
				grat_december_proy = 0
				record.contrac_proy_rem = 0
			else:
				if Contract.date_start.year == date.today().year:
					if Contract.date_start.month == 12:
						grat_july_proy = 0
						grat_december_proy = 0
					elif Contract.date_start.month >= 7:
						grat_july_proy = 0
						if Contract.date_start.day == 1:
							grat_december_proy = ((record.monthly_rem * (1 + (Contract.social_insurance_id.percent) / 100)) / 6) * (13 - Contract.date_start.month)
						else:
							grat_december_proy = ((record.monthly_rem * (1 + (Contract.social_insurance_id.percent) / 100)) / 6) * (12 - Contract.date_start.month)
					else:
						if Contract.date_start.day == 1:
							grat_july_proy = ((record.monthly_rem * (1 + (Contract.social_insurance_id.percent) / 100)) / 6) * (7 - Contract.date_start.month)
						else:
							grat_july_proy = ((record.monthly_rem * (1 + (Contract.social_insurance_id.percent) / 100)) / 6) * (6 - Contract.date_start.month)
						grat_december_proy = record.monthly_rem * (1 + (Contract.social_insurance_id.percent) / 100)
				else:
					grat_july_proy = record.monthly_rem * (1 + (Contract.social_insurance_id.percent) / 100)
					grat_december_proy = record.monthly_rem * (1 + (Contract.social_insurance_id.percent) / 100)

				record.contrac_proy_rem = record.monthly_rem if MainParameter.compute_proy_planilla else Contract.fifth_rem_proyected

			grat_july_proy = grat_july_proy if MainParameter.compute_proy_planilla else Contract.grat_july_proyected
			grat_december_proy = grat_december_proy if MainParameter.compute_proy_planilla else Contract.grat_december_proyected

			record.proy_rem = record.contrac_proy_rem * proy_month + record.monthly_rem
			record.grat_july = (grat_july.total_grat + grat_july.bonus_essalud) if month >= 7 and grat_july else grat_july_proy
			record.grat_december = (grat_december.total_grat + grat_december.bonus_essalud) if month == 12 and grat_december else grat_december_proy
			record.past_rem = self.get_past_rem(Slip, FiscalYear.date_from)
			record.total_proy = record.proy_rem + record.grat_july + record.grat_december + record.other_emp_proy_rem + record.past_rem
			record.seven_uit = 7 * uit
			record.net_rent = record.total_proy - record.seven_uit
			tax_proy = self.get_tax_proy(record.net_rent, MainParameter.rate_limit_ids)
			record.tax_proy = 0 if tax_proy < 0 else tax_proy
			record.past_months_ret = self.get_past_months_ret(Slip, FiscalYear.date_from)
			record.annual_ret = record.tax_proy - record.past_months_ret - record.other_emp_ret
			record.monthly_rent = ReportBase.custom_round(record.annual_ret/rent_month, 2)
			record.ext_rem = Slip.line_ids.filtered(lambda line: line.salary_rule_id == MainParameter.fifth_extr_sr_id).total
			record.total_net_rent = record.ext_rem + record.net_rent
			ext_ret = self.get_tax_proy(record.total_net_rent, MainParameter.rate_limit_ids) - record.tax_proy
			record.ext_ret = 0 if ext_ret < 0 else ext_ret
			record.monthly_ret = record.monthly_rent + record.ext_ret
			if not record.monthly_ret > 0 and not self._context.get('line_form', False) and record.fifth_category_id.state=='draft':
				data={
					'fifth_category_id': record.fifth_category_id.id,
					'slip_id':record.slip_id.id,
					'monthly_rem':record.monthly_rem,
					'contrac_proy_rem': record.contrac_proy_rem,
					'proy_rem': record.proy_rem,
					'grat_july': record.grat_july,
					'grat_december': record.grat_december,
					'total_proy': record.total_proy,
					'seven_uit': record.seven_uit,
					'net_rent': record.net_rent,
				}
				# print("data",data)
				self.env['hr.fifth.category.line.excluidos'].create(data)
				record.unlink()


class HrFifthCategoryLineExcluidos(models.Model):
	_name = 'hr.fifth.category.line.excluidos'
	_description = 'Fifth Category Line Excluidos'
	_rec_name = 'employee_id'

	fifth_category_id = fields.Many2one('hr.fifth.category', ondelete='cascade')
	slip_id = fields.Many2one('hr.payslip', string='Nomina', required=True)
	employee_id = fields.Many2one(related='slip_id.employee_id', string='Empleado', required=True)
	identification_id = fields.Char(related='slip_id.employee_id.identification_id', string='N° Identificacion')
	monthly_rem = fields.Float(string='Remuneracion Mensual')
	contrac_proy_rem = fields.Float(string='Rem. Proy. Segun Contrato', help='Remuneracion Proyectada Segun Contrato')
	proy_rem = fields.Float(string='Remuneracion Proyectada')
	grat_july = fields.Float(string='Gratificacion Julio')
	grat_december = fields.Float(string='Gratificacion Diciembre')
	total_proy = fields.Float(string='Total Proyectado')
	seven_uit = fields.Float(string='Deduccion 7 UIT')
	net_rent = fields.Float(string='Renta Neta')