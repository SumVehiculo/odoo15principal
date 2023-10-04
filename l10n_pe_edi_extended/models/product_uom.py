# coding: utf-8
from odoo import api, fields, models, _


class ProductUom(models.Model):
    _inherit = 'uom.uom'

    l10n_pe_edi_unece = fields.Char(string=u'Código UN/ECE rec 20')