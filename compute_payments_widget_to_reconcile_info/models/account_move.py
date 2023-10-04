# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.tools import float_is_zero, float_compare, safe_eval, date_utils, email_split, email_escape_char, email_re
from json import dumps
import json

class AccountMove(models.Model):
	_inherit = "account.move"

	def _compute_payments_widget_to_reconcile_info(self):
		for move in self:
			move.invoice_outstanding_credits_debits_widget = json.dumps(False)
			move.invoice_has_outstanding = False

			if move.state != 'posted' \
					or move.payment_state not in ('not_paid', 'partial') \
					or not move.is_invoice(include_receipts=True):
				continue

			pay_term_lines = move.line_ids\
				.filtered(lambda line: line.account_id.user_type_id.type in ('receivable', 'payable'))

			domain = [
				('account_id', 'in', pay_term_lines.account_id.ids),
				('parent_state', '=', 'posted'),
				('partner_id', '=', move.commercial_partner_id.id),
				('reconciled', '=', False),
				'|', ('amount_residual', '!=', 0.0), ('amount_residual_currency', '!=', 0.0),
				('type_document_id', '=', move.l10n_latam_document_type_id.id),
				('nro_comp', '=', move.ref)
			]

			payments_widget_vals = {'outstanding': True, 'content': [], 'move_id': move.id}

			if move.is_inbound():
				domain.append(('balance', '<', 0.0))
				payments_widget_vals['title'] = _('Outstanding credits')
			else:
				domain.append(('balance', '>', 0.0))
				payments_widget_vals['title'] = _('Outstanding debits')

			for line in self.env['account.move.line'].search(domain):

				if line.currency_id == move.currency_id:
					# Same foreign currency.
					amount = abs(line.amount_residual_currency)
				else:
					# Different foreign currencies.
					amount = move.company_currency_id._convert(
						abs(line.amount_residual),
						move.currency_id,
						move.company_id,
						line.date,
					)

				if move.currency_id.is_zero(amount):
					continue

				payments_widget_vals['content'].append({
					'journal_name': line.ref or line.move_id.name,
					'amount': amount,
					'currency': move.currency_id.symbol,
					'id': line.id,
					'move_id': line.move_id.id,
					'position': move.currency_id.position,
					'digits': [69, move.currency_id.decimal_places],
					'payment_date': fields.Date.to_string(line.date),
				})

			if not payments_widget_vals['content']:
				continue

			move.invoice_outstanding_credits_debits_widget = json.dumps(payments_widget_vals)
			move.invoice_has_outstanding = True