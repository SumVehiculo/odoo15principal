from odoo   import models, fields, api, _
from odoo.exceptions import UserError

class StockMove(models.Model):
    _inherit="stock.move"
    
    work_order_id = fields.Many2one('project.project', string='Orden de Trabajo')