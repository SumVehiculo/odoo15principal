# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError

class AccountMove(models.Model):
    _inherit = 'account.move'

    def _auto_create_asset(self):
        assets = super(AccountMove, self)._auto_create_asset()
        if assets:
            if self.partner_id:
                assets.partner_id= self.partner_id.id
        return assets

