# -*- coding: utf-8 -*-

from ast import Pass
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo import tools


class stock_picking(models.Model):
    _inherit = 'stock.picking'
    
    @api.model
    def create(self,vals):
        if self.move_ids_without_package.analytic_account_id == False or self.move_ids_without_package.analytic_tag_id == False:
            if self.move_ids_without_package.analytic_account_id == False:
                raise UserError("Falta completar Cuenta Analítica")
            if self.move_ids_without_package.analytic_tag_id == False:
                raise UserError("Falta completar Etiqueta Analítica")
        else:
            t = super(stock_picking,self).create(vals)
            return t
        
    def write(self,vals):
        if self.move_ids_without_package.analytic_account_id == False or self.move_ids_without_package.analytic_tag_id == False:
            if self.move_ids_without_package.analytic_account_id == False:
                raise UserError("Falta completar Cuenta Analítica")
            if self.move_ids_without_package.analytic_tag_id == False:
                raise UserError("Falta completar Etiqueta Analítica")
        else:
            t = super(stock_picking,self).write(vals)
            return t
       