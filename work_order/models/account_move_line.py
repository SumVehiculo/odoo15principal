from odoo   import models, fields, api, _
from odoo.exceptions import UserError

class AccountMoveLine(models.Model):
    _inherit="account.move.line"
    
    work_order_id = fields.Many2one('project.project', string='Orden de Trabajo')