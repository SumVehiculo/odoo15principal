from odoo import models, fields, api, _
from odoo.exceptions import UserError

class SaleOrderLine(models.Model):
    _inherit="sale.order.line"
    
    @api.model
    def create(self, vals):
        res=super().create(vals)
        if not res.analytic_tag_ids:
            raise UserError("Es necesaria la Etiqueta analitica")
        return res
    
    def write(self, vals):
        res = super().write(vals)
        if not self.analytic_tag_ids:
            raise UserError("Es necesaria la Etiqueta analitica")
        return res