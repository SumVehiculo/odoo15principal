# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class AccountInvoiceLine(models.Model):
	_inherit = 'account.move.line'

	def asset_create(self):
		asset = super(AccountInvoiceLine, self).asset_create()
		if self.asset_category_id:
			amount = self.price_subtotal
			if self.move_id.currency_id.name != 'PEN':
				amount = self.price_subtotal * self.move_id.currency_rate
		asset.date_at = self.move_id.invoice_date
		asset.valor_at = amount
		return asset