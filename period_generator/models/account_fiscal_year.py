# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError
from datetime import date

class AccountFiscalYear(models.Model):
	_inherit = 'account.fiscal.year'

	def generate_periods(self):
		wiz = self.env['period.generator'].create({
			'fiscal_year_id': self.id
		})
		return wiz.generate_periods()