# coding: utf-8
from odoo import api, fields, models, _


class StockLocation(models.Model):
    _inherit = 'stock.location'

    l10n_pe_edi_branch_code = fields.Char(string=u'Código Establecimiento Anexo')