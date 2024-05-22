from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountMoveLine(models.Model):
    _inherit="account.move.line"
    
    @api.model
    def create(self, vals):
        res=super().create(vals)
        if res.invoice_line_ids.sale_line_ids and not res.analytic_tag_id:
            raise UserError(f"Es necesaria la Cuenta analitica para una Factura de Venta")
        return res
    
    def write(self, vals):
        # Si es una Venta Nacional
        res = super().write(vals)
        if self.invoice_line_ids.sale_line_ids and not self.analytic_tag_id:
            raise UserError(f"Es necesaria la Cuenta analitica para una Factura de Venta")
        return res