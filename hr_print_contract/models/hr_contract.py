# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from datetime import date
from dateutil.relativedelta import relativedelta

class hr_contract(models.Model):
	_inherit = 'hr.contract'

	trial_date_end = fields.Date(compute='_get_periodo_prueba', store=True)
	date_first_contract = fields.Date(string='Fecha Contrato Original')

	@api.depends('date_start')
	def _get_periodo_prueba(self):
		for record in self:
			if record.date_start:
				record.trial_date_end = record.date_start + relativedelta(months=3)

	def export_contract(self):
		return self.env.ref('hr_print_contract.action_report_contract_employee').report_action(self)

	def send_contract_email(self):
		for rec in self:
			template = self.env.ref('hr_print_contract.report_contract_employee')
			email_values = {
				'email_to': rec.employee_id.work_email,
			}
			template.send_mail(rec.id, force_send=True, email_values=email_values)

class ContractType(models.Model):
	_inherit = 'hr.contract.type'

	contract_html = fields.Html('Contrato')