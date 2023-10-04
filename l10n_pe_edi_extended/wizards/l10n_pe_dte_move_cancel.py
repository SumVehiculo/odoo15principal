# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

class L10nPeDteMoveCancel(models.TransientModel):
    _name = 'l10n_pe_dte.move.cancel'
    _description = 'Send DTE cancel'
    
    description = fields.Char('Reason')
    
    def send_invoice_cancel(self):
        #getting invoice_ids selected
        active_ids = self.env.context.get('active_ids',[])
        for move in active_ids:
            #calling method "invoice_send_cancel" sending invoice
            self.env['account.move'].browse(move).with_context(reason=self.description).l10n_pe_dte_action_cancel()