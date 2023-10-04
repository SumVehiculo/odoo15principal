# -*- coding:utf-8 -*-
from odoo import api, fields, models

class HrPayslipInputType(models.Model):
	_inherit = 'hr.payslip.input.type'

	company_id = fields.Many2one('res.company', string=u'Compañia', default=lambda self: self.env.company.id)
	active = fields.Boolean(string='Activo', default=True)

	@api.model
	def delete_input(self):
		for data_input in self.env['hr.payslip.input.type'].search([('code','in',['DEDUCTION','REIMBURSEMENT','ATTACH_SALARY','ASSIG_SALARY','CHILD_SUPPORT'])]):
			data_input.active = False