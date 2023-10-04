# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import UserError

import logging
log = logging.getLogger(__name__)

class AccountJournal(models.Model):
    _inherit = "account.journal"

    l10n_pe_is_dte = fields.Boolean(string='Is DTE?', copy=False)

