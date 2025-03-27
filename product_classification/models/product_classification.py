from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

class ProductClassification(models.Model):
    _name = 'product.classification'
    _description = 'Clasificacion de Productos'

    name = fields.Char('Nombre')
    