# -*- coding: utf-8 -*-
from odoo import models

class AccountMove(models.Model):
    _inherit = "account.move"

    def _l10n_pe_prepare_dte(self):
        res = super(AccountMove, self)._l10n_pe_prepare_dte()
        res['company_branch_id'] = self.company_branch_address_id.address_external_id if self.company_branch_address_id else False
        return res