# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.tools.translate import _

class AccountMoveReversal(models.TransientModel):
	_inherit = 'account.move.reversal'

	def _prepare_default_reversal(self, move):
		res = super(AccountMoveReversal, self)._prepare_default_reversal(move)
		credit_note = self.env['account.main.parameter'].search([('company_id', '=', self.env.company.id)],
														limit=1).dt_national_credit_note

		res['ref'] = credit_note._get_ref(self.reason) if self.reason else ''
		res['currency_rate'] = move.currency_rate
		res['glosa'] = 'Anulacion de '+(move.glosa or '')
		res['l10n_latam_document_type_id'] = credit_note.id or None
		res['serie_id'] = None
		res['doc_invoice_relac'] = [(0, 0, {'type_document_id': move.l10n_latam_document_type_id.id,
											  'date': move.invoice_date,
											  'nro_comprobante': move.ref,
											  'amount_currency': move.amount_total if move.currency_id.name != 'PEN' else 0,
											  'amount': abs(move.amount_total_signed)}
											)]
		return res