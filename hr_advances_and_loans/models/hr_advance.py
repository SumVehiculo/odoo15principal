# -*- coding:utf-8 -*-
from odoo import api, fields, models, tools
from odoo.exceptions import UserError

class HrAdvanceType(models.Model):
	_name = 'hr.advance.type'
	_description = 'Advance Type'

	name = fields.Char(string='Nombre')
	input_id = fields.Many2one('hr.payslip.input.type', string='Input de Planillas')
	# salary_rule_id = fields.Many2one('hr.salary.rule', string='Concepto Remunerativo')
	company_id = fields.Many2one('res.company', string='Compañia', default=lambda self: self.env.company.id)

class HrAdvance(models.Model):
	_name = 'hr.advance'
	_description = 'Advance'

	name = fields.Char()
	company_id = fields.Many2one('res.company', string='Compañia', default=lambda self: self.env.company.id, required=True, states={'paid out': [('readonly', True)]})
	employee_id = fields.Many2one('hr.employee', string='Empleado', states={'paid out': [('readonly', True)]})
	amount = fields.Float(string='Monto', states={'paid out': [('readonly', True)]})
	date = fields.Date(string='Fecha de Adelanto', states={'paid out': [('readonly', True)]})
	discount_date = fields.Date(string='Fecha de Descuento', states={'paid out': [('readonly', True)]})
	advance_type_id = fields.Many2one('hr.advance.type', string='Tipo de Adelanto', states={'paid out': [('readonly', True)]})
	state = fields.Selection([('not payed', 'No Pagado'), ('paid out', 'Pagado')], default='not payed',string='Estado')

	active = fields.Boolean(string='Activo', default=True)

	def turn_paid_out(self):
		for record in self:
			record.state = 'paid out'

	def set_not_payed(self):
		self.state = 'not payed'

	@api.onchange('employee_id', 'advance_type_id')
	def _get_name(self):
		for record in self:
			if record.advance_type_id and record.employee_id:
				record.name = '%s %s' % (record.advance_type_id.name, record.employee_id.name)

	def unlink(self):
		for advance in self:
			if advance.state in ('paid out'):
				raise UserError("No puedes eliminar una adelanto que ya fue Aplicado.")
		return super(HrAdvance, self).unlink()