# -*- coding:utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.tools import format_date

class HrPayslipEmployees(models.TransientModel):
	_inherit = 'hr.payslip.employees'

	def _get_available_contracts_domain(self):
		return [('contract_ids.state', 'in', ('open', 'close')), ('company_id', '=', self.env.company.id)]
		# return [('contract_ids.state', 'in', ('open', 'close'))]

	structure_id = fields.Many2one(domain=lambda self:[('company_id', '=', self.env.company.id)],
								   default=lambda self: self.get_structure_id())
	type_id = fields.Many2one('hr.payroll.structure.type', required=True)

	def get_structure_id(self):
		return self.env['hr.payroll.structure'].search([('schedule_pay', '=', 'monthly'),('active', '=',True),('company_id', '=', self.env.company.id)],limit=1).id


	@api.depends('type_id')
	def _compute_employee_ids(self):
		for wizard in self:
			domain = wizard._get_available_contracts_domain()
			# if wizard.type_id:
			# 	domain = [('contract_ids.structure_type_id', '=', self.type_id.id)]
				# print("domain",domain)
			wizard.employee_ids = self.env['hr.employee'].search(domain)

	def compute_sheet(self):
		self.ensure_one()
		if not self.env.context.get('active_id'):
			from_date = fields.Date.to_date(self.env.context.get('default_date_start'))
			end_date = fields.Date.to_date(self.env.context.get('default_date_end'))
			payslip_run = self.env['hr.payslip.run'].create({
				'name': from_date.strftime('%B %Y'),
				'date_start': from_date,
				'date_end': end_date,
			})
		else:
			payslip_run = self.env['hr.payslip.run'].browse(self.env.context.get('active_id'))

		if not self.employee_ids:
			raise UserError("Debe seleccionar empleado(s) para generar una nomina.")

		payslips = self.env['hr.payslip']
		Payslip = self.env['hr.payslip']

		contracts = self.employee_ids._get_contracts(payslip_run.date_start, payslip_run.date_end, states=['open', 'close'])
		# print("contracts",contracts)

		MainParameter = self.env['hr.main.parameter'].get_main_parameter()

		default_values = Payslip.default_get(Payslip.fields_get())
		for contract in contracts:
			values = dict(default_values, **{
				'name': 'Recibo Nomina - %s - %s' % (contract.employee_id.name or '',payslip_run.name.name or ''),
				'employee_id': contract.employee_id.id,
				'identification_id': contract.employee_id.identification_id,
				'credit_note': payslip_run.credit_note,
				'payslip_run_id': payslip_run.id,
				'date_from': payslip_run.date_start,
				'date_to': payslip_run.date_end,
				'contract_id': contract.id,
				'struct_id': self.structure_id.id or contract.structure_type_id.id,
				'struct_type_id': self.type_id.id,
				'wage': contract.wage,
				'labor_regime': contract.labor_regime,
				'social_insurance_id': contract.social_insurance_id.id,
				'distribution_id': contract.distribution_id.id,
				'workday_id': contract.workday_id.id,
				'membership_id': contract.membership_id.id,
				'commision_type': contract.commision_type,
				'fixed_commision': contract.membership_id.fixed_commision,
				'mixed_commision': contract.membership_id.mixed_commision,
				'prima_insurance': contract.membership_id.prima_insurance,
				'retirement_fund': contract.membership_id.retirement_fund,
				'insurable_remuneration': contract.membership_id.insurable_remuneration,
				'is_afp': contract.membership_id.is_afp,
				'rmv': MainParameter.rmv,
				'company_id': self.env.company.id
			})

			payslip = self.env['hr.payslip'].new(values)
			# payslip._onchange_employee()
			values = payslip._convert_to_write(payslip._cache)
			# values['company_id']=self.env.company.id
			# print("values",values)
			payslips += Payslip.create(values)
		
		payslips.generate_inputs_and_wd_lines()
		payslips.compute_sheet()
		payslip_run.state = 'verify'

		return {
			'type': 'ir.actions.act_window',
			'res_model': 'hr.payslip.run',
			'views': [[False, 'form']],
			'res_id': payslip_run.id,
		}