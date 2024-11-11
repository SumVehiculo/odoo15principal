from odoo import models, fields, api
from odoo.exceptions import UserError

class AccountMove(models.Model):
    _inherit="account.move"

    sale_labels = fields.Text('Pedido Nro',compute="_compute_sale_labels", store=True)
    sale_date_order = fields.Datetime('Fecha Pedido',compute="_compute_sale_date_order", store=True)
    
    @api.depends('invoice_line_ids')
    def _compute_sale_labels(self):
        for invoice in self:            
            invoice.sale_labels = '/n'.join([line.name for line in invoice.invoice_line_ids.sale_line_ids.order_id])

    @api.depends('invoice_line_ids')
    def _compute_sale_date_order(self):
        for invoice in self:
            sale_orders=invoice.invoice_line_ids.sale_line_ids.order_id
            invoice.sale_date_order = sale_orders[0] if sale_orders else False