# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
log = logging.getLogger(__name__)

class ResCompany(models.Model):
    _inherit = "res.company"

    l10n_pe_dte_service_provider = fields.Selection(selection_add=[('CONFLUX', 'CONFLUX - Online')])
    l10n_pe_dte_conflux_client_id = fields.Char(string='Conflux-ClientID')
    l10n_pe_dte_conflux_token = fields.Char(string='Conflux-Token')