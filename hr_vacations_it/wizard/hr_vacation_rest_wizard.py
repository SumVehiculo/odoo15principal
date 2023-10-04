# -*- coding:utf-8 -*-
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
import datetime

class hr_vacation_rest_wizard(models.TransientModel):
	_name='hr.vacation.rest.wizard'
	_description='Hr Vacation Rest Wizard'

	employee_id = fields.Many2one('hr.employee','Empleado', default=lambda self: self.env['hr.employee'].sudo().search([('user_id','=',self.env.user.id)]) )
	showall = fields.Boolean('Mostrar Todos',default=True)

	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	# fiscal_year_id = fields.Many2one('account.fiscal.year',string='Ejercicio',required=True)


	def make_vacation_rest(self):
		self.env['hr.vacation.rest'].get_vacation_employee(self.employee_id,self.showall)
		name = 'Saldos de Vacaciones'
		if self.showall:
			domain=[('company_id','=',self.env.company.id)]
		else:
			domain=[('company_id','=',self.env.company.id),('employee_id','=',self.employee_id.id)]
		c={
			'name': name,
			'type': 'ir.actions.act_window',
			'res_model': 'hr.vacation.rest',
			'view_type': 'form',
			'view_mode': 'tree',
			'views': [(False, 'tree')],
			'search_view_id':[self.env.ref('hr_vacations_it.hr_vacation_rest_search').id, 'search'],
			'domain':domain
			}
		# print(c)
		return c