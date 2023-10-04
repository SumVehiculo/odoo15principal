# -*- coding:utf-8 -*-
from odoo import api, fields, models

class HrSuspensionType(models.Model):
	_name = 'hr.suspension.type'
	_description = 'Suspension Type'

	code = fields.Char(string='Codigo')
	description = fields.Char(string='Descripcion')
	name = fields.Char(string='Abreviacion')