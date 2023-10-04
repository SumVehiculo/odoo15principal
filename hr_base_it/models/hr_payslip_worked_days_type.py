# -*- coding:utf-8 -*-
from odoo import api, fields, models

class HrPayslipWorkedDaysType(models.Model):
	_name = 'hr.payslip.worked_days.type'
	_description = 'Payslip Worked Days Type'

	company_id = fields.Many2one('res.company', string=u'Compañia', default=lambda self: self.env.company.id, required=True)
	name = fields.Char(string='Descripcion')
	code = fields.Char(string='Codigo')
	days = fields.Integer(string='Numero de Dias')
	hours = fields.Float(string='Numero de Horas')
	rate = fields.Integer(string='Tasa o Monto')
	struct_ids = fields.Many2many('hr.payroll.structure', 'payroll_structure_wd_rel', 'worked_day_type_id', 'structure_id', string='Disponibilidad de la Estructura')