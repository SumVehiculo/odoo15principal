# -*- coding: utf-8 -*-

from ast import Pass
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo import tools


class stock_picking(models.Model):
    _inherit = 'stock.picking'
    
    @api.model
    def create(self, vals):
        if vals.get('type_operation_sunat_id') in ('10', '91', '92'):
            move_ids_without_package = vals.get('move_ids_without_package') or []
            for move in move_ids_without_package:
                if not move.get('analytic_account_id') or not move.get('analytic_tag_id'):
                    raise UserError("Falta completar Cuenta Analítica o Etiqueta Analítica")
        
        res = super(stock_picking, self).create(vals)
        return res
        
    def write(self, vals):
        if self.type_operation_sunat_id.code in ('10', '91', '92'):
            for move in self.move_ids_without_package:
                if not move.analytic_account_id or not move.analytic_tag_id:
                    raise UserError("Falta completar Cuenta Analítica o Etiqueta Analítica")
        res = super(stock_picking, self).write(vals)
        return res
       