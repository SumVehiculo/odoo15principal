# -*- coding:utf-8 -*-
from odoo import api, fields, models

class HrSalaryRule(models.Model):
	_inherit = 'hr.salary.rule'

	is_detail_cta = fields.Boolean(string='Detallar esta Cuenta', default=False)