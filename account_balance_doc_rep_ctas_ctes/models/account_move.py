# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class AccountMoveLine(models.Model):
	_inherit = 'account.move.line'

	#invoice_date_it = fields.Date(string=u'Fecha Emisión')
	#cta_cte_origen = fields.Boolean(string=u'Es cta cte Origen',default=False)

class AccountMove(models.Model):
	_inherit = 'account.move'

	def _post(self, soft=True):
		posted = super()._post(soft)
		for move in posted:
			if move.move_type != 'entry':
				for line in move.line_ids.filtered(
						lambda l: l.account_id.internal_type in ['receivable', 'payable']):
					line.cta_cte_origen = True
					line.invoice_date_it = move.invoice_date
		return posted