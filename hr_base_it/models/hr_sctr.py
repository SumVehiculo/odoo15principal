# -*- coding:utf-8 -*-
from odoo import api, fields, models

class HrSctr(models.Model):
	_name = 'hr.sctr'
	_description = 'Sctr'

	percent = fields.Float(string='%', digits=(12,2))
	name = fields.Char(string='Descripcion', required=True)
	code = fields.Char(string='Codigo', required=True)