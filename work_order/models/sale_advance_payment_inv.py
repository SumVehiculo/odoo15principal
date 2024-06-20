from odoo   import models, fields, api, _
from odoo.exceptions import UserError

class SaleAdvancePaymentInv(models.Model):
    _inherit="sale.advance.payment.inv"
    
    def create_invoices(self):
        active_sale = self.env['sale.order'].browse(self._context.get('active_id', False))
        new_invoices = active_sale.invoice_ids
        res = super().create_invoices()
        new_invoices = active_sale.invoice_ids - new_invoices
        
        for invoice in new_invoices:
            for line in invoice.invoice_line_ids:
                work_order_id = line.sale_line_ids.work_order_id 
                if not work_order_id:
                    continue
                line.write({
                    'work_order_id':work_order_id[0].id 
                })
            pass
        return res