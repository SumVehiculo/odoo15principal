# -*- coding:utf-8 -*-
from odoo import api, fields, models

class HrSocialInsurance(models.Model):
	_name = 'hr.social.insurance'
	_description = 'Social Insurance'

	percent = fields.Float(string='%', digits=(12,2))
	name = fields.Char(string='Seguro')