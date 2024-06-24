from odoo   import models, fields, api, _
from odoo.exceptions import UserError

class SaleOrder(models.Model):
    _inherit="sale.order"
    
    def action_confirm(self):
        for res in self:
            new_picks = res.picking_ids
            rec = super().action_confirm()
            new_picks = res.picking_ids - new_picks
            for pick in new_picks:
                for line in pick.move_ids_without_package:
                    line.write({
                        'work_order_id': line.sale_line_id.work_order_id.id
                    })
            return rec