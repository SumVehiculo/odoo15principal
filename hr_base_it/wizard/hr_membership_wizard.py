# -*- coding:utf-8 -*-
from odoo import api, fields, models

class HrMembershipWizard(models.TransientModel):
	_name = 'hr.membership.wizard'
	_description = 'Hr Membership Wizard'

	name = fields.Char()
	company_ids = fields.Many2many('res.company', string='Compañias')
	fixed_commision = fields.Float(string='Comision Sobre Flujo %')
	mixed_commision = fields.Float(string='Comision Mixta %')
	prima_insurance = fields.Float(string='Prima de Seguros %')
	retirement_fund = fields.Float(string='Aporte Fondo de Pensiones %')
	insurable_remuneration = fields.Float(string='Remuneracion Asegurable')

	def duplicate_by_company(self):
		Memberships = self.env['hr.membership'].browse(self._context.get('active_ids'))
		for rec in Memberships:
			for comp in self.company_ids:
				acc = self.env['account.account'].search([('company_id', '=', comp.id), ('code', '=', rec.account_id.code)])
				rec.copy(default={'company_id': comp.id, 'account_id': acc.id if acc else None})

	def edit_by_company(self):
		Memberships = self.env['hr.membership'].browse(self._context.get('active_ids'))
		for rec in Memberships:
			for comp in self.company_ids:
				mem = self.env['hr.membership'].search([('name', '=', rec.name), ('company_id', '=', comp.id)])
				mem.write({
					'fixed_commision': self.fixed_commision,
					'mixed_commision': self.mixed_commision,
					'prima_insurance': self.prima_insurance,
					'retirement_fund': self.retirement_fund,
					'insurable_remuneration': self.insurable_remuneration,
					})