# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class MultipaymentAdvanceIt(models.Model):
	_inherit = 'multipayment.advance.it'

	account_date = fields.Date(string='Fecha Contable')

	@api.onchange('payment_date')
	def on_change_payment_date_retention(self):
		if self.payment_date:
			self.account_date = self.payment_date