# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError



class AccountMainParameter(models.Model):
	_inherit = 'account.main.parameter'

	
	max_detracion = fields.Float(string='Monto Detracción',default=700)
