# -*- coding:utf-8 -*-
from odoo import api, fields, models

class HrHolidays(models.Model):
	_name = 'hr.holidays'
	_description = 'Holidays'

	name = fields.Char(compute='_get_name', string='Nombre')
	date = fields.Date(string='Fecha', required=True)
	workday_id = fields.Many2one('hr.workday', string='Jornada Laboral', required=True)

	def _get_name(self):
		for record in self:
			record.name = record.date