# -*- coding:utf-8 -*-
from odoo import api, fields, models

class HrSalaryRule(models.Model):
	_inherit = 'hr.salary.rule'

	company_id = fields.Many2one('res.company', string=u'Compañia', default=lambda self: self.env.company.id)
	sunat_code = fields.Char(string='Codigo SUNAT')
	# is_subtotal = fields.Boolean(string='Es un Subtotal', default=False)

	@api.model
	def store_salary_rules(self):
		for rule in self.env['hr.salary.rule'].search([('code','in',['BASIC','GROSS','NET','ATTACH_SALARY','ASSIG_SALARY','CHILD_SUPPORT','DEDUCTION','REIMBURSEMENT'])]):
			rule.active = False
		self.env['ir.translation'].search([('src', '=', 'Bachelor'), ('module', '=', 'hr')]).value = 'Bachiller'