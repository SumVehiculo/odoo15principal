# -*- coding:utf-8 -*-
from odoo import api, fields, models

class HrWorkday(models.Model):
	_name = 'hr.workday'
	_description = 'Workday'

	code = fields.Char(string='Codigo')
	name = fields.Char(string='Descripcion')
	days = fields.Integer(string="N° de Dias")
	record_days = fields.Integer(string="Dias Record Vacacional")