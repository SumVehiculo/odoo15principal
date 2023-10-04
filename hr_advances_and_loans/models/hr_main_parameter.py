# -*- coding:utf-8 -*-
from odoo import api, fields, models

class HrMainParameter(models.Model):
	_inherit = 'hr.main.parameter'

	grat_advance_id = fields.Many2one('hr.advance.type', string='Tipo de Adelanto')
	cts_advance_id = fields.Many2one('hr.advance.type', string='Tipo de Adelanto')
	liqui_advance_id = fields.Many2one('hr.advance.type', string='Tipo de Adelanto')
	vaca_advance_id = fields.Many2one('hr.advance.type', string='Tipo de Adelanto')

	grat_loan_id = fields.Many2one('hr.loan.type', string='Tipo de Prestamo')
	cts_loan_id = fields.Many2one('hr.loan.type', string='Tipo de Prestamo')
	liqui_loan_id = fields.Many2one('hr.loan.type', string='Tipo de Prestamo')
	vaca_loan_id = fields.Many2one('hr.loan.type', string='Tipo de Prestamo')