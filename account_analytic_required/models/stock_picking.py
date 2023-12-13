# -*- coding: utf-8 -*-

from ast import Pass
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo import tools


class stock_picking(models.Model):
    _inherit = 'stock.picking'
    
    @api.model
    def create(self, vals):
       
        res = super(stock_picking, self).create(vals)
        res.move_ids_without_package.verify_required()
        return res
        
    def write(self, vals):
       
        res = super(stock_picking, self).write(vals)
        self.move_ids_without_package.verify_required()
        return res

class stock_move(models.Model):
    _inherit = 'stock.move'
    
    def verify_required(self):
        if self.picking_id.type_operation_sunat_id.code in ('10', '91', '92'):
            for move in self:
                if not move.analytic_account_id or not move.analytic_tag_id:
                    raise UserError("Falta completar Cuenta Analítica o Etiqueta Analítica")
       
        return

    @api.model
    def create(self, vals):
        res = super(stock_move, self).create(vals)
        res.verify_required()
        return res
        
    def write(self, vals):
        res = super(stock_move, self).write(vals)
        self.verify_required()
        return res
       