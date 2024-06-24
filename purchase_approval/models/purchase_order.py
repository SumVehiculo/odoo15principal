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
    
    
    unconfirmed_by = fields.Many2one(
        'res.users',
        string='Desaprobado por',
        copy=False
    )           
    date_unconfirmed = fields.Datetime(
        'Fecha de Desaprobación',
        copy=False
    )
    
    custom_approve = fields.Boolean('Aprobacion customizada', default=False)
    
    
    def button_confirm(self):
        res = super().button_confirm()
        # for rec in self:
        #     if not rec.custom_approve:
        #         raise UserError("La compra necesita ser aprobada. ")
        return res
        
    def button_custom_confirm(self):
        if not self.env.user.has_group("purchase_approval.purchase_approval_group"):
            raise UserError(f"Usted no tiene suficientes permisos para aprobar esta compra.")
        self.write({
            'confirmed_by' : self.env.user.id,
            'date_confirmed' : datetime.now() - timedelta(hours=5),
            'custom_approve': True
        })

    def button_custom_unconfirm(self):
        if not self.env.user.has_group("purchase_approval.purchase_approval_group"):
            raise UserError(f"Usted no tiene suficientes permisos para desaprobar esta compra.")
        if self.state != 'draft':
            raise UserError(f"Solo se puede desaprobar compras en estado Borrador")
        self.write({
            'unconfirmed_by' : self.env.user.id,
            'date_unconfirmed' : datetime.now() - timedelta(hours=5),
            'custom_approve': False
        })
