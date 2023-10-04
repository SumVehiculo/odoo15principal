# -*- coding:utf-8 -*-
from odoo import api, fields, models

class HrMembership(models.Model):
	_name = 'hr.membership'
	_description = 'Membership'

	name = fields.Char(string='Entidad')	
	company_id = fields.Many2one('res.company', string=u'Compañía', default=lambda self: self.env.company.id)
	fixed_commision = fields.Float(string='Comision Sobre Flujo %')
	mixed_commision = fields.Float(string='Comision Mixta %')
	prima_insurance = fields.Float(string='Prima de Seguros %')
	retirement_fund = fields.Float(string='Aporte Fondo de Pensiones %')
	insurable_remuneration = fields.Float(string='Remuneracion Asegurable')
	account_id = fields.Many2one('account.account', string='Cuenta Contable')
	is_afp = fields.Boolean(string='Es AFP', default=False)

	def get_membership_wizard(self):
		wizard = self.env['hr.membership.wizard'].create({'name':'Generacion de Afiliaciones'})
		return {
			'type':'ir.actions.act_window',
			'res_id':wizard.id,
			'view_mode':'form',
			'res_model':'hr.membership.wizard',
			'views':[[self.env.ref('hr_base_it.hr_membership_wizard_form').id,'form']],
			'context': self._context,
			'target':'new'
		}

	def get_membership_wizard_edit(self):
		wizard = self.env['hr.membership.wizard'].create({'name':'Generacion de Afiliaciones'})
		return {
			'type':'ir.actions.act_window',
			'res_id':wizard.id,
			'view_mode':'form',
			'res_model':'hr.membership.wizard',
			'views':[[self.env.ref('hr_base_it.hr_membership_wizard_form_edit').id,'form']],
			'context': self._context,
			'target':'new'
		}