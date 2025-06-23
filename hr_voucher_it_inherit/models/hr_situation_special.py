# -*- coding:utf-8 -*-
from odoo import api, fields, models

class HrSituationSpecial(models.Model):
	_name = 'hr.situation.special'
	_description = 'Situation special'

	code = fields.Char(string='Codigo')
	description = fields.Char(string='Descripcion')
	name = fields.Char(string='Abreviacion')