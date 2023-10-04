# -*- coding:utf-8 -*-
from odoo import api, fields, models

class HrWorkerType(models.Model):
	_name = 'hr.worker.type'
	_description = 'Worker Type'

	code = fields.Char(string='Codigo')
	description = fields.Char(string='Descripcion')
	name = fields.Char(string='Abreviacion')