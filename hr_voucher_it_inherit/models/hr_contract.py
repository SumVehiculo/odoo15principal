# -*- coding:utf-8 -*-
from datetime import date, datetime, time
from odoo import api, fields, models

class HrContract(models.Model):
	_inherit = 'hr.contract'

	situation_special_id = fields.Many2one('hr.situation.special', string='Calificacion del Trabajador', help='TABLA 35 SUNAT')