# -*- coding:utf-8 -*-
from odoo import api, fields, models

class HrSalaryRuleCategory(models.Model):
	_inherit = 'hr.salary.rule.category'

	active = fields.Boolean(string='Activo', default=True)
	sequence = fields.Integer(string='Secuencia')
	type = fields.Selection([('in','Ingreso'),('out','Descuento')], string='Tipo')
	appears_on_payslip = fields.Boolean(string='Aparece en la Nomina', default=False)

	@api.model
	def store_salary_rules_categories(self):
		for category in self.env['hr.salary.rule.category'].search([('code','in',['BASIC','ALW','GROSS','DED','NET','COMP'])]):
			category.active = False