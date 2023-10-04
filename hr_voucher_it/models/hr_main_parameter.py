# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError
from datetime import *
from collections import Counter

class HrMainParameter(models.Model):
	_inherit = 'hr.main.parameter'

	type_boleta = fields.Selection([('1', 'Formato Boleta de Pago N° 01'),
							 ('2', 'Formato Boleta de Pago N° 02')], string='Formato de Boleta', default='1' )