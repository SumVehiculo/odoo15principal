# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging
log = logging.getLogger(__name__)

class AccountDebitNote(models.TransientModel):

    _inherit = 'account.debit.note'
    
    l10n_pe_dte_debit_note_type = fields.Selection(
        selection=[
            ('01', 'Intereses por mora'),
            ('02', 'Aumento en el valor'),
            ('03', 'Penalidades/ otros conceptos '),
            ('11', 'Ajustes de operaciones de exportación'),
            ('12', 'Ajustes afectos al IVAP'),
        ],
        string="Debit Note Type")

    def _prepare_default_values(self, move):
        values = super()._prepare_default_values(move)
        values.update({
            'l10n_pe_dte_debit_note_type': self.l10n_pe_dte_debit_note_type or '02',
            'l10n_pe_dte_rectification_ref_date': move.invoice_date or False,
        })
        if move.l10n_latam_use_documents:
            values.update({
                'l10n_latam_document_type_id': self.env.ref('l10n_pe_extended.document_type08b').id if move.l10n_latam_document_type_id.code=='03' else self.env.ref('l10n_pe.document_type08').id,
                'l10n_pe_dte_rectification_ref_type':move.l10n_latam_document_type_id.id,
                'l10n_pe_dte_rectification_ref_number':move.l10n_latam_document_number,
            })
        return values
