# -*- coding: utf-8 -*-

from odoo import models
import logging
log = logging.getLogger(__name__)

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _prepare_invoice_line(self, **optional_values):
        res = super(SaleOrderLine, self)._prepare_invoice_line(**optional_values)
        self.ensure_one()
        if self.is_downpayment and res.get('l10n_pe_dte_advance_line', False):
            if len(self.invoice_lines)>0:
                invoice = self.invoice_lines.filtered(lambda i: i.move_id.state not in ('cancel'))
                if invoice[0].ref:
                    invoice_seq = invoice[0].ref.split('-')
                    if len(invoice_seq)==2:
                        res['l10n_pe_dte_advance_serial'] = invoice_seq[0]
                        res['l10n_pe_dte_advance_number'] = invoice_seq[1]
        log.info(res)
        return res