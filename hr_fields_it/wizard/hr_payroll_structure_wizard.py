# -*- coding:utf-8 -*-
from odoo import api, fields, models

class HrPayrollStructureWizard(models.TransientModel):
	_name = 'hr.payroll.structure.wizard'
	_description = 'Hr Payroll Structure Wizard'

	name = fields.Char()
	company_ids = fields.Many2many('res.company', string="compañias")

	def generate_structures(self):
		for company in self.company_ids:
			struct = self.env['hr.payroll.structure'].browse(self.env.context['active_id'])
			copied_rules = []
			copied_struct = struct.copy(default={'rule_ids': None, 
												 'input_line_type_ids': None, 
												 'wd_types_ids': None})
			copied_struct.company_id = company.id
			for rule in struct.rule_ids:
				copied_rule = rule.copy(default={'struct_id': copied_struct.id})
				copied_rule.company_id = company.id
				copied_rules.append(copied_rule.id)
			copied_inputs = []
			for input in struct.input_line_type_ids:
				copied_input = input.copy(default={'struct_ids': [(6, 0, copied_struct.ids)]})
				copied_input.company_id = company.id
				copied_inputs.append(copied_input.id)
			copied_wds = []
			for wd in struct.wd_types_ids:
				copied_wd = wd.copy(default={'struct_ids': [(6, 0, copied_struct.ids)]})
				copied_wd.company_id = company.id
				copied_wds.append(copied_wd.id)
			copied_struct.rule_ids = [(6, 0, copied_rules)]
			copied_struct.input_line_type_ids = [(6, 0, copied_inputs)]
			copied_struct.wd_types_ids = [(6, 0, copied_wds)]
		return self.env['popup.it'].get_message("SE GENERARON LAS ESTRUCTURAS SALARIALES DE MANERA CORRECTA")