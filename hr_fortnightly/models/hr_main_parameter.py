# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError

class HrMainParameter(models.Model):
	_inherit = 'hr.main.parameter'

	# hr_advance_type_id = fields.Many2one('hr.advance.type','Tipo de Adelanto')
	quin_input_id = fields.Many2one('hr.payslip.input.type', string='Input Quincena')
	percentage = fields.Float(string='Porcentaje',digits=(12,2))
	compute_afiliacion = fields.Boolean(string="Calcular Afiliacion", default=False)

	quin_advance_id = fields.Many2one('hr.advance.type', string='Tipo de Adelanto')
	quin_loan_id = fields.Many2one('hr.loan.type', string='Tipo de Prestamo')

	def check_quincena_values(self):
		if not self.quin_input_id or \
			not self.percentage:
			raise UserError(u'Faltan Configuraciones en la Pestaña de Adelantos Quincenales del Menu de Parametros Principales')