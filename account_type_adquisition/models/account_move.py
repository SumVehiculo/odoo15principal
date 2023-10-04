# -*- coding: utf-8 -*-

from odoo import models, api, _
from odoo.exceptions import UserError

class AccountMove(models.Model):
	_inherit = "account.move"

	def _post(self, soft=True):
		posted = super()._post(soft)
		for inv in posted:
			if len(inv.invoice_line_ids)>0 and inv.move_type in ('in_invoice','in_refund'):
				inv.campo_34_purchase = inv.invoice_line_ids[len(inv.invoice_line_ids)-1].account_id.type_adquisition
		return posted