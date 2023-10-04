# -*- coding: utf-8 -*-

from odoo import fields, models


class ResConfigSettings(models.TransientModel):

    _inherit = 'res.config.settings'

    l10n_pe_dte_conflux_client_id = fields.Char(related='company_id.l10n_pe_dte_conflux_client_id', readonly=False)
    l10n_pe_dte_conflux_token = fields.Char(related='company_id.l10n_pe_dte_conflux_token', readonly=False)