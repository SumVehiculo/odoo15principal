# -*- coding:utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError

class HrMainParameter(models.Model):
	_inherit = 'hr.main.parameter'

	day_limit = fields.Integer(string="Limite Dias", default=10)
