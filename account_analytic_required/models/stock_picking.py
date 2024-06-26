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
        # Update 6/26/24  Ticket(#27083)
        # al momento de cancelar la SDP da error por transferencias con distintos tipos de operaciones
        # Linea eliminada:
        # if self.picking_id.type_operation_sunat_id.code in ('10', '91', '92'):
        if any([pick.code in ('10', '91', '92') for pick in self.picking_id.type_operation_sunat_id]):
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
    
class sale_order(models.Model):
    _inherit = 'sale.order'
    
    factura = fields.Boolean(
        string='Tiene factura', 
        default= False    
    )

    def tiene_factura(self):
        if self.invoice_ids >= 1:
            self.factura = True
        else:
            self.factura = False

class sale_order_line(models.Model):
    _inherit = 'sale.order.line'
    
    line_factura = fields.Boolean(
        string='Tiene factura', 
        default= False
        
    )

    def tiene_lfactura(self):
       for i in self:
           self.line_factura = self.order_id.factura