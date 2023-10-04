# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import models, fields, api


class purchase_order(models.Model):
    _inherit = "purchase.order"
    
    def sh_import_pol(self):
        if self:
            action = self.env.ref('import_purchase_order_line.sh_import_pol_action').read()[0]
            return action             
            
