from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountMoveLine(models.Model):
    _inherit="account.move.line"
    
    @api.model
    def create(self, vals):
        res=super().create(vals)
        if not res.sale_line_ids:
            res.sale_line_ids=res.move_id.invoice_line_ids.sale_line_ids
        if res.move_id.invoice_line_ids.sale_line_ids and not res.analytic_tag_ids:
            raise UserError(f"Es necesaria la Etiqueta analitica para una Factura de Venta")
        return res
    
    def write(self, vals):
        # Si es una Venta Nacional
        res = super().write(vals)
        if self.sale_line_ids and not self.analytic_tag_ids:
            raise UserError(f"Es necesaria la Etiqueta analitica para una Factura de Venta")
        return res