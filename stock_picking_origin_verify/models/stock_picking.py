# -*- coding: utf-8 -*-

from ast import Pass
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo import tools


class stock_picking(models.Model):
    _inherit = 'stock.picking'
    
    
    @api.constrains('location_id','location_dest_id')
    def _check_not_same_dest(self):
        for i in self:
            if i.location_id.id and i.location_dest_id.id  and i.state == 'done':
                if i.location_id.id == i.location_dest_id.id:
                    raise UserError("No puede Guardar Albaranes con la misma Ubicación Origen y Destino")
                
class stock_move(models.Model):
    _inherit = 'stock.move'
    
    @api.constrains('location_id','location_dest_id')
    def _check_not_same_dest_move(self):
        for i in self:
            if i.location_id.id and i.location_dest_id.id and i.state == 'done':
                if i.location_id.id == i.location_dest_id.id:
                    raise UserError("No puede Guardar Albaranes con la misma Ubicación Origen y Destino")
                
class stock_move_line(models.Model):
    _inherit = 'stock.move.line'
    
    @api.constrains('location_id','location_dest_id')
    def _check_not_same_dest_line(self):
        for i in self:
            if i.location_id.id and i.location_dest_id.id  and i.state == 'done':
                if i.location_id.id == i.location_dest_id.id:
                    raise UserError("No puede Guardar Albaranes con la misma Ubicación Origen y Destino")
