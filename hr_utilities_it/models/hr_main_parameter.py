# -*- coding:utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError

class HrMainParameter(models.Model):
	_inherit = 'hr.main.parameter'

	rule_total_income = fields.Many2one('hr.salary.rule', string='Rem. Afecta Utilidades')
	wd_dtrab = fields.Many2many('hr.payslip.worked_days.type', 'wd_dtrab_main_parameter_rel', 'main_parameter_id', 'wd_id', string='Worked Days Dias Trabajados')
	wd_falt = fields.Many2many('hr.payslip.worked_days.type', 'wd_falt_main_parameter_rel', 'main_parameter_id', 'wd_id', string='Worked Days Faltas')
	hr_input_for_results = fields.Many2one('hr.payslip.input.type', string='Input Utilidades')
	# legal_representative = fields.Char(string='Representante Legal')

	def check_utility_values(self):
		if not self.rule_total_income or \
				not self.wd_dtrab or \
				not self.wd_falt or \
				not self.reprentante_legal_id or \
				not self.hr_input_for_results:
			raise UserError(u'Faltan Configuraciones en la Pestaña de Utilidades del Menu de Parametros Principales')