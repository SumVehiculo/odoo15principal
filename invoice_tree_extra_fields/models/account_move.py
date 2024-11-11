from odoo import models, fields, api
from odoo.exceptions import UserError

class AccountMove(models.Model):
    _inherit="account.move"

    sale_labels = fields.Text('Pedido Nro',compute="_compute_sale_labels")
    sale_date_order = fields.Text('Fecha Pedido',compute="_compute_sale_date_order")

    @api.depends('invoice_line_ids')
    def _compute_sale_labels(self):
        for invoice in self:            
            invoice.sale_labels = '/n'.join([line.name for line in invoice.invoice_line_ids.sale_line_ids.order_id])

    @api.depends('invoice_line_ids')
    def _compute_sale_date_order(self):
        for invoice in self:
            invoice.sale_date_order = '/n'.join([line.date_order.strftime('%d/%m/%Y') for line in invoice.invoice_line_ids.sale_line_ids.order_id])