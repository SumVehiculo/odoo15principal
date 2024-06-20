from odoo   import models, fields, api, _
from odoo.exceptions import UserError

class SaleOrderLine(models.Model):
    _inherit="sale.order.line"
    
    work_order_id = fields.Many2one('project.project', string='Orden de Trabajo')