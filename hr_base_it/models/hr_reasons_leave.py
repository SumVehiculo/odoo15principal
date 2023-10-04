# -*- coding:utf-8 -*-
from odoo import api, fields, models

class HrReasonsLeave(models.Model):
	_name = 'hr.reasons.leave'
	_description = 'Hr Reasons Leave'

	code = fields.Char(string='Codigo')
	description = fields.Char(string='Descripcion')
	name = fields.Char(string='Abreviacion')