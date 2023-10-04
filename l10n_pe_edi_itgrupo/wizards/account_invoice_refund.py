# -*- coding: utf-8 -*-
from odoo import api, fields, models
import logging
log = logging.getLogger(__name__)

class AccountMoveReversal(models.TransientModel):
    _inherit = 'account.move.reversal'

    def _prepare_default_reversal(self, move):
        values = super()._prepare_default_reversal(move)
        values.update({
            'l10n_latam_document_type_id': self.env.ref('l10n_pe.document_type07b').id if move.l10n_latam_document_type_id.code=='03' else self.env.ref('l10n_pe.document_type07').id,
            'l10n_pe_dte_rectification_ref_type':move.l10n_latam_document_type_id.id,
            'l10n_pe_dte_rectification_ref_number':move.ref,
        })
        return values