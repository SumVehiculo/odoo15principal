# -*- coding: utf-8 -*-

from ast import Pass
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo import tools

class stock_warehouse(models.Model):
    _inherit = 'stock.warehouse'
    
    
    def unlink(self):
        if self.env.user.has_group("stock_warehouse_restriction.group_stock_warehouse_restriction"):
            t = super(stock_warehouse,self).unlink()
            return t
        else:
            raise UserError("No Tiene Los Permisos de 'Manejo Almacen Ubicacion y tipo operacion'")

    @api.model
    def create(self,vals):
        if self.env.user.has_group("stock_warehouse_restriction.group_stock_warehouse_restriction"):
            t = super(stock_warehouse,self).create(vals)
            return t
        else:
            raise UserError("No Tiene Los Permisos de 'Manejo Almacen Ubicacion y tipo operacion'")
           
    def write(self,vals):
        if self.env.user.has_group("stock_warehouse_restriction.group_stock_warehouse_restriction"):
            t = super(stock_warehouse,self).write(vals)
            return t
        else:
            raise UserError("No Tiene Los Permisos de 'Manejo Almacen Ubicacion y tipo operacion'")

class stock_location(models.Model):
    _inherit = 'stock.location'
    
    def unlink(self):
        if self.env.user.has_group("stock_warehouse_restriction.group_stock_warehouse_restriction"):
            t = super(stock_location,self).unlink()
            return t
        else:
            raise UserError("No Tiene Los Permisos de 'Manejo Almacen Ubicacion y tipo operacion'")
    
    @api.model
    def create(self,vals):
        if self.env.user.has_group("stock_warehouse_restriction.group_stock_warehouse_restriction"):
            t = super(stock_location,self).create(vals)
            return t
        else:
            raise UserError("No Tiene Los Permisos de 'Manejo Almacen Ubicacion y tipo operacion'")
           
    def write(self,vals):
        if self.env.user.has_group("stock_warehouse_restriction.group_stock_warehouse_restriction"):
            t = super(stock_location,self).write(vals)
            return t
        else:
            raise UserError("No Tiene Los Permisos de 'Manejo Almacen Ubicacion y tipo operacion'")
        
class stock_picking_type(models.Model):
    _inherit = 'stock.picking.type'
    
    def unlink(self):
        if self.env.user.has_group("stock_warehouse_restriction.group_stock_warehouse_restriction"):
            t = super(stock_picking_type,self).unlink()
            return t
        else:
            raise UserError("No Tiene Los Permisos de 'Manejo Almacen Ubicacion y tipo operacion'")
    
    @api.model
    def create(self,vals):
        if self.env.user.has_group("stock_warehouse_restriction.group_stock_warehouse_restriction"):
            t = super(stock_picking_type,self).create(vals)
            return t
        else:
            raise UserError("No Tiene Los Permisos de 'Manejo Almacen Ubicacion y tipo operacion'")
           
    def write(self,vals):
        if self.env.user.has_group("stock_warehouse_restriction.group_stock_warehouse_restriction"):
            t = super(stock_picking_type,self).write(vals)
            return t
        else:
            raise UserError("No Tiene Los Permisos de 'Manejo Almacen Ubicacion y tipo operacion'")
