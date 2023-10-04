# coding: utf-8
from odoo import api, fields, models, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    l10n_pe_dte_mtc_authorization = fields.Char(string='Autorizacion MTC')