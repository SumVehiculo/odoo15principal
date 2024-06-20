from odoo   import models, fields, api, _
from odoo.exceptions import UserError

class PurchaseOrder(models.Model):
    _inherit="purchase.order"
    
    def button_confirm(self):
        for rec in self:
            new_picks = rec.picking_ids
            res = super().button_confirm()
            new_picks = rec.picking_ids - new_picks
            for pick in new_picks:
                for line in pick.move_ids_without_package:
                    line.write({
                        'work_order_id': line.purchase_line_id.work_order_id.id
                    })
            return res 
    
    def action_create_invoice(self):
        new_invoices = self.invoice_ids
        res = super().action_create_invoice()
        new_invoices = self.invoice_ids - new_invoices
        for invoice in new_invoices:
            for line in invoice.invoice_line_ids:
                line.write({
                    'work_order_id':line.purchase_line_id.work_order_id.id
                })
        return res