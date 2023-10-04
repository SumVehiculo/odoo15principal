# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

import logging
log = logging.getLogger(__name__)

class AccountMovePaymentFee(models.Model):
    _name = 'account.move.payment_fee'

    @api.model
    def _get_default_currency(self):
        invoice_currency = self.move_id.currency_id
        return invoice_currency

    sequence = fields.Integer(string='Sequence')
    move_id = fields.Many2one('account.move')
    currency_id = fields.Many2one('res.currency', store=True,
        string='Currency',
        default=_get_default_currency)
    amount_total = fields.Monetary(string='Total', required=True)
    date_due = fields.Date(string='Due Date', required=True)