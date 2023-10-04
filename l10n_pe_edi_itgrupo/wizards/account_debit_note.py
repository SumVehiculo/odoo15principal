# -*- coding: utf-8 -*-
from odoo import api, fields, models
import logging
log = logging.getLogger(__name__)

class AccountDebitNote(models.TransientModel):
    _inherit = 'account.debit.note'

    def _prepare_default_values(self, move):
        values = super()._prepare_default_values(move)
        values.update({
            'l10n_latam_document_type_id': self.env.ref('l10n_pe_extended.document_type08b').id if move.l10n_latam_document_type_id.code=='03' else self.env.ref('l10n_pe.document_type08').id,
            'l10n_pe_dte_rectification_ref_type':move.l10n_latam_document_type_id.id,
            'l10n_pe_dte_rectification_ref_number':move.ref,
        })
        return values


    '''def create_debit(self):
        res = super(AccountDebitNote, self).create_debit()
        if res.get('res_id', False):
            debit = self.env['account.move'].browse(res.get('res_id'))
            if debit:
                debit.write({
                    'l10n_pe_dte_rectification_ref_number': debit.debit_origin_id.ref,
                    'doc_invoice_relac': [(0, 0, {
                        'type_document_id': debit.debit_origin_id.l10n_latam_document_type_id.id,
                        'date': debit.debit_origin_id.invoice_date,
                        'nro_comprobante': debit.debit_origin_id.ref,
                        'amount_currency': debit.debit_origin_id.amount_total if debit.debit_origin_id.currency_id.name != 'PEN' else 0,
                        'amount': abs(debit.debit_origin_id.amount_total_signed),
                        'bas_amount': abs(debit.debit_origin_id.amount_untaxed),
                        'tax_amount': abs(debit.debit_origin_id.amount_total_signed - debit.debit_origin_id.amount_untaxed)
                    })]
                })
        return res'''