# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class AccountMoveLine(models.Model):
	_inherit = 'account.move.line'

	amount_c = fields.Float(string='Importe Conversion',digits=(64,2))