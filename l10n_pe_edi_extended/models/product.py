# coding: utf-8
from odoo import api, fields, models, _


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    l10n_pe_edi_unspsc = fields.Char(string=u'Código UNSPSC v14_0801')