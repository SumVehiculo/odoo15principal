# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo import tools

class stock_move(models.Model):
    _inherit = 'stock.move'

    def write(self,vals):
        if 'state' in vals and vals['state']=='done':
            for i in self:
                i.verify_quantites_available()
        t = super(stock_move,self).write(vals)
        return t

    def verify_quantites_available(self):
        for i in self:
            i.refresh()
            if True:
                if i.location_id.usage == 'internal' or i.location_id.usage == 'transit':
                    for stock_move_line in i.move_line_ids:
                        if stock_move_line.product_id.tracking == 'serial' or stock_move_line.product_id.tracking == 'lot':
                            if stock_move_line.lot_id.id:
                                verify_quants = self.env["stock.quant"].sudo().search([('product_id','=',stock_move_line.product_id.id), ('company_id', '=', i.company_id.id), ('location_id', '=', stock_move_line.location_id.id),('lot_id', '=', stock_move_line.lot_id.id)])
                            else:
                                raise UserError("No Hay Cantidades Suficientes Para Confirmar Esta Operación, Ya Que Los Lotes Recien Los Esta Creando Con Cantidad 0. Producto: " +str(stock_move_line.product_id.default_code))
                        else:
                            verify_quants = self.env["stock.quant"].sudo().search([('product_id','=',stock_move_line.product_id.id), ('company_id', '=', i.company_id.id), ('location_id', '=', stock_move_line.location_id.id)])
                        if len(verify_quants)>0:
                            for q in verify_quants:
                                if q.quantity < 0:
                                    msg_extra = ""
                                    if stock_move_line.lot_id.id:
                                        msg_extra += ", Del Lote: " + str(stock_move_line.lot_id.name)
                                    raise UserError("No Hay Cantidades Suficientes Para Confirmar Esta Operación, Producto: "+str(stock_move_line.product_id.default_code) + ", Ubicación: "+str(stock_move_line.location_id.name_get()[0][1]) + msg_extra + ", cantidades Faltante: " + str(q.quantity))
                        else:
                            return