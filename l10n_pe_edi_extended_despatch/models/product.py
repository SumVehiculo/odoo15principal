# coding: utf-8
from odoo import api, fields, models, _


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    l10n_pe_edi_gtin = fields.Char(string=u'Código GTIN')
    l10n_pe_edi_normalized_good = fields.Boolean(string=u'Bien Normalizado')
    l10n_pe_edi_tariff_code = fields.Char(string='Partida Arancelaria')