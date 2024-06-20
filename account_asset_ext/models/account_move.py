# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError

class AccountMove(models.Model):
    _inherit = 'account.move'

    def _auto_create_asset(self):
        assets = super(AccountMove, self)._auto_create_asset()
        raise UserError(str(assets))
        

