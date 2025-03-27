from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    classification_id = fields.Many2one('product.classification', string='Clasificación')
    