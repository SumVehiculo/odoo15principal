from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

class KardexFisicoIt(models.Model):
    _inherit = 'stock.picking'

    invoice_id = fields.Many2one(
        'account.move',
        'Factura',
        domain=[('move_type', 'in', ['out_invoice','in_invoice','out_refund','in_refund'])],
        tracking=True
    )    