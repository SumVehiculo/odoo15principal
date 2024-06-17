from odoo   import models, fields, api, _
from odoo.exceptions import UserError

class PurchaseOrderLine(models.Model):
    _inherit="purchase.order.line"
    
    work_order_id = fields.Many2one('project.project', string='Orden de Trabajo')