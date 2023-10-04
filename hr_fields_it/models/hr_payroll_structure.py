# -*- coding: utf-8 -*-

from odoo import api, fields, models

class HrPayrollStructure(models.Model):
	_inherit = 'hr.payroll.structure'

	company_id = fields.Many2one('res.company', string=u'Compañia', default=lambda self: self.env.company.id)
	wd_types_ids = fields.Many2many('hr.payslip.worked_days.type', 'payroll_structure_wd_rel', 'structure_id', 'worked_day_type_id')

	def get_wizard(self):
		wizard = self.env['hr.payroll.structure.wizard'].create({'name':'Generacion de Estructuras'})
		return {
			'type':'ir.actions.act_window',
			'res_id':wizard.id,
			'view_mode':'form',
			'res_model':'hr.payroll.structure.wizard',
			'views':[[self.env.ref('hr_fields_it.hr_payroll_structure_wizard_form_inherit').id,'form']],
			'target':'new'
		}