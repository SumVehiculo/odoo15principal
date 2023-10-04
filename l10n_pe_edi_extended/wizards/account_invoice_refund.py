# -*- coding: utf-8 -*-
from odoo import api, fields, models
import logging
log = logging.getLogger(__name__)

class AccountMoveReversal(models.TransientModel):
    _inherit = 'account.move.reversal'

    l10n_pe_dte_credit_note_type = fields.Selection(
        selection=[
            ('01', 'Anulación de la operación'),
            ('02', 'Anulación por error en el RUC'),
            ('03', 'Corrección por error en la descripción'),
            ('04', 'Descuento global'),
            ('05', 'Descuento por ítem'),
            ('06', 'Devolución total'),
            ('07', 'Devolución por ítem'),
            ('08', 'Bonificación'),
            ('09', 'Disminución en el valor'),
            ('10', 'Otros Conceptos '),
            ('11', 'Ajustes de operaciones de exportación'),
            ('12', 'Ajustes afectos al IVAP'),
            ('13', 'Ajustes – montos y/o fechas de pago'),
        ],
        string="Credit Note Type")

    def _prepare_default_reversal(self, move):
        log.info('PRUEBA***************************************')
        values = super()._prepare_default_reversal(move)
        values.update({
            'l10n_pe_dte_credit_note_type': self.l10n_pe_dte_credit_note_type or '01',
            'l10n_pe_dte_rectification_ref_date': move.invoice_date or False,
        })
        if move.l10n_latam_use_documents:
            values.update({
                'l10n_latam_document_type_id': self.env.ref('l10n_pe.document_type07b').id if move.l10n_latam_document_type_id.code=='03' else self.env.ref('l10n_pe.document_type07').id,
                'l10n_pe_dte_rectification_ref_type':move.l10n_latam_document_type_id.id,
                'l10n_pe_dte_rectification_ref_number':move.l10n_latam_document_number,
            })
        return values