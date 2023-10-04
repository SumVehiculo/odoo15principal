# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class AccounthPayment(models.Model):
	_inherit = "account.payment"

	amount_mn = fields.Float(string='Monto MN',digits=(12,2),compute='_calculate_amounts')
	amount_me = fields.Monetary(string='Monto ME',digits=(12,2),compute='_calculate_amounts')

	@api.onchange('manual_batch_payment_id')
	def get_batch_data(self):
		if self.manual_batch_payment_id:
			self.cash_nro_comp = self.manual_batch_payment_id.name or ''
			self.journal_id = self.manual_batch_payment_id.journal_id or self.journal_id
			self.catalog_payment_id = self.manual_batch_payment_id.catalog_payment_id or self.catalog_payment_id
			self.date = self.manual_batch_payment_id.date
			self.ref = self.manual_batch_payment_id.glosa

	@api.depends('amount',
				'type_change',
				'currency_id')
	def _calculate_amounts(self):
		for payment in self:
			payment.amount_mn = (payment.amount * payment.type_change) if payment.currency_id != payment.company_id.currency_id else payment.amount
			payment.amount_me = payment.amount if payment.currency_id != payment.company_id.currency_id else None