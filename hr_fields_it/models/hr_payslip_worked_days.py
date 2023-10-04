# -*- coding:utf-8 -*-
from odoo import api, fields, models

class HrPayslipWorkedDays(models.Model):
	_inherit = 'hr.payslip.worked_days'

	wd_type_id = fields.Many2one('hr.payslip.worked_days.type', string='Tipo de Worked Day')
	name = fields.Char(related='wd_type_id.name')
	code = fields.Char(related='wd_type_id.code')
	rate = fields.Integer(related='wd_type_id.rate', string='Tasa o Monto')
	work_entry_type_id = fields.Many2one('hr.work.entry.type', string='Type', required=False, help="El código que se puede utilizar en las reglas salariales.")

	# name = fields.Char(compute='')
	amount = fields.Monetary(compute='')
	is_paid = fields.Boolean(compute='')