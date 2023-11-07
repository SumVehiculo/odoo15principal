# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class product_category(models.Model):
    _inherit = "product.category"

    empresa_field = fields.Selection(selection=[('sum', 'SUM'),('sumas', 'SUMMAS'),('csi', 'CSI'),], string='Empresa',default='draft')
