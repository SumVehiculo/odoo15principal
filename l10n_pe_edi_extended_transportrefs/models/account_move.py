# -*- encoding: utf-8 -*-
from odoo import models, fields, api, _
import logging
log = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = 'account.move'

    l10n_pe_dte_transportref_ids = fields.One2many(
        'account.move.transportref', 'move_id', string='Guias de remisión Adjuntas', copy=True)

    def _l10n_pe_prepare_dte(self):
        res = super(AccountInvoice, self)._l10n_pe_prepare_dte()
        if self.l10n_pe_dte_transportref_ids:
            res['remission_guides'] = []
            for guide in self.l10n_pe_dte_transportref_ids:
                res['remission_guides'].append({
                    'type':guide.ref_type,
                    'number': '%s-%s' % (guide.ref_serial, guide.ref_number),
                })
        return res

class AccountInvoiceTransportReferences(models.Model):
    _name = 'account.move.transportref'

    move_id = fields.Many2one(
        'account.move', string='Invoice', ondelete='cascade', index=True)
    ref_type = fields.Selection([('09', 'GR REMITENTE'), (
        '31', 'GR TRANSPORTISTA')], string="Tipo", default='09')
    ref_serial = fields.Char('Serie de Guia', required=True, default='')
    ref_number = fields.Char('Numero', required=True, default='')