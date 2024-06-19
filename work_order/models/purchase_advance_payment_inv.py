from odoo   import models, fields, api, _
from odoo.exceptions import UserError

class PurchaseAdvancePaymentInv(models.TransientModel):
    _inherit="purchase.advance.payment.inv"
    
    def create_invoices(self):
        purchase = self.env['purchase.order'].browse(self._context.get('active_id', False))
        res = super().create_invoices()
        invoices = purchase.invoice_ids
        raise UserError(f"invoices {invoices}")
        return res