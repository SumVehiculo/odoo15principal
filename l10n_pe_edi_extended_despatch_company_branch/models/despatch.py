# -*- encoding: utf-8 -*-
from odoo import fields, api, models, _
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
import requests
import json
import datetime

import logging
log = logging.getLogger(__name__)


class LogisticDespatch(models.Model):
    _inherit = 'logistic.despatch'

    def _l10n_pe_prepare_dte(self):
        res = super(LogisticDespatch, self)._l10n_pe_prepare_dte()
        res['establecimiento_anexo'] = self.journal_id.company_branch_address_id.address_external_id if self.journal_id.company_branch_address_id else False
        return res