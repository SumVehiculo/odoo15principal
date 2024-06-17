from odoo   import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta

class PurchaseOrder(models.Model):
    _inherit="purchase.order"
    
    approved_by = fields.Many2one(
        'res.users',
        string='Aprobado por',
        copy=False
    )
    
    def approve_purchase(self):
        if not self.env.user.has_group(""):
            raise UserError(f"Usted no tiene permisos suficientes para aprobar esta compra.")
        self.write({
            'state' : 'approve',
            'approved_by' : self.env.user.id,
            'approve_date' : datetime.today() + timedelta(hours="5")
        })
        
    def button_approve(self, force=False):
        result = super().button_approve(force)
        if self.state == 'purchase':
            self.write({
                'date_approve' : datetime.now() - timedelta(hours=5),
                'approved_by' : self.env.user.id
            })
        return result