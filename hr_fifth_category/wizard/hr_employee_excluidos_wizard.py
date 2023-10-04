# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _


class HrEmployeeExcluidosWizard(models.TransientModel):
	_name = 'hr.employee.excluidos.wizard'
	_description = 'Hr Employee Excluidos Wizard'

	fifth_category_id = fields.Many2one('hr.fifth.category', string='P. Multiple')
	company_id = fields.Many2one('res.company', string=u'Compañia', required=True,
								 default=lambda self: self.env.company, readonly=True)
	employees = fields.Many2many('hr.fifth.category.line.excluidos', 'hr_fifth_category_employee_excluidos_rel','fifth_category_id','employee_id',
								 string=u'Empleados Excluidos', required=True,
								 domain="[('fifth_category_id','=',fifth_category_id)]")

	def insert(self):
		vals = []
		for employee in self.employees:
			val = {
				'fifth_category_id': self.fifth_category_id.id,
				'slip_id':employee.slip_id.id,
				# 'monthly_rem':employee.monthly_rem,
				# 'contrac_proy_rem': employee.contrac_proy_rem,
				# 'proy_rem': employee.proy_rem,
				# 'grat_july': employee.grat_july,
				# 'grat_december': employee.grat_december,
				# 'total_proy': employee.total_proy,
				# 'seven_uit': employee.seven_uit,
				# 'net_rent': employee.net_rent,
			}
			vals.append(val)
		self.env['hr.fifth.category.line'].create(vals)