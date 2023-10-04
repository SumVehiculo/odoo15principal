# -*- coding:utf-8 -*-
from odoo import api, fields, models

class HrSituation(models.Model):
	_name = 'hr.situation'
	_description = 'Situation'

	code = fields.Char(string='Codigo')
	description = fields.Char(string='Descripcion')
	name = fields.Char(string='Abreviacion')