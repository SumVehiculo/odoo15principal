# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError

class HrPayslip(models.Model):
	_inherit = 'hr.payslip'

	def get_import_wd_wizard(self):
		wizard = self.env['hr.import.wd.wizard'].create({'name': 'Import WD'})
		return {
			'type': 'ir.actions.act_window',
			'res_id': wizard.id,
			'view_mode': 'form',
			'res_model': 'hr.import.wd.wizard',
			'views': [[self.env.ref('hr_importers_it.hr_import_wd_wizard_form').id,'form']],
			'target': 'new',
			'context': {'payslip_ids': self.ids}
		}