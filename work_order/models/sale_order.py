from odoo   import models, fields, api, _
from odoo.exceptions import UserError

class SaleOrder(models.Model):
    _inherit="sale.order"
    
    def action_confirm(self):
        pass