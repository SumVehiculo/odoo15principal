from odoo   import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta

class PurchaseOrder(models.Model):
    _inherit="purchase.order"
    
    confirmed_by = fields.Many2one(
        'res.users',
        string='Aprobado por',
        copy=False
    )           
    date_confirmed = fields.Datetime(
        'Fecha de Aprobación',
        copy=False
    )
    
    def button_confirm(self):
        res = super().button_confirm()
        for rec in self:
            if not rec.confirmed_by:
                raise UserError("La compra necesita ser aprobada. ")
        return res
        
    def button_approve(self):
        if not self.env.user.has_group("purchase_approval.purchase_approval_group"):
            raise UserError(f"Usted no tiene suficientes permisos para aprobar esta compra.")
        self.write({
            'confirmed_by' : datetime.now() - timedelta(hours=5),
            'date_confirmed' : self.env.user.id
        })