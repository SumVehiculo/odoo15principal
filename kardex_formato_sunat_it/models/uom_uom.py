from odoo import api, fields, models
class UomUom(models.Model):
    _inherit               = 'uom.uom'
    code_sunat             = fields.Many2one('einvoice.catalog.13',string="Codigo Sunat")