from odoo import models, fields, api, _
from odoo.exceptions import UserError


class StockMove(models.Model):
    _inherit="stock.move"
    
    
    
    @api.model
    def create(self, vals):
        res = super().create(vals)
        if res.picking_id.type_operation_sunat_id.code == '01' and not res.analytic_tag_id:
            raise UserError(f"Es necesaria la Etiqueta Analitica para una VENTA NACIONAL")
        return res
    
    def write(self, vals):
        # Si es una Venta Nacional
        res = super().write(vals)
        if self.picking_id.type_operation_sunat_id.code == '01' and not self.analytic_tag_id:
            raise UserError(f"Es necesaria la Etiqueta Analitica para una VENTA NACIONAL")
        return res