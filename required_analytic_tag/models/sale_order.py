from odoo import models, fields, api, _
from odoo.exceptions import UserError

class SaleOrder(models.Model):
    _inherit="sale.order"
    
    @api.model
    def create(self, vals):
        res=super().create(vals)
        if not res.analytic_account_id:
            raise UserError("Es necesaria la Cuenta analitica")
        for line in res.order_line:
            if not line.analytic_tag_ids and not line.display_type:
                raise UserError(f"El producto{line.product_id.name}no tiene una Etiqueta analitica")    
        return res
    
    def write(self, vals):
        res = super().write(vals)
        if not self.analytic_account_id:
            raise UserError("Es necesaria la Cuenta analitica")
        for line in self.order_line:
            if not line.analytic_tag_ids and not line.display_type:
                raise UserError(f"El producto{line.product_id.name}Es necesaria la Etiqueta analitica")    
        return res