from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class stock_location(models.Model):
    _inherit = 'stock.location'

    use_in_transit = fields.Boolean(string="Se usa en Transito",copy=False)

#    @api.constrains("use_in_transit","company_id")
#    def _check_field_model(self):
#        for i in self:
#            if i.use_in_transit:
#                if i.company_id.id:
#                    for srch in i.env["stock.location"].sudo().search([("company_id","in",[False,i.company_id.id]),("use_in_transit","=",True),("id","!=",i.id)]):
#                        raise UserError("Solo Puede Existir 1 ubicacion para usar en transito")
#                else:
#                    for srch in i.env["stock.location"].sudo().search([("use_in_transit","=",True),("id","!=",i.id)]):
#                        raise UserError("Solo Puede Existir 1 ubicacion para usar en transito")





class stock_picking_type(models.Model):
    _inherit = 'stock.picking.type'
    usar_en_recepciondetransito = fields.Boolean(string="Usar en recepcion de Transito",copy=False)




class stock_move(models.Model):
    _inherit = 'stock.move'
    origin_move_id = fields.Many2one("stock.move",string="Transito Origen Detalle",copy=False)



class stock_picking(models.Model):
    _inherit = 'stock.picking'
    op_sunat_transito = fields.Boolean(string="OP Sunat Transito",compute="verify_op_sunat_transito",store=True)
    origin_transit_id = fields.Many2one("stock.picking",string="Transito Origen",copy=False)
    destiny_transit_id = fields.One2many("stock.picking","origin_transit_id",string="Transitos Creados",copy=False)

    @api.depends("picking_type_id","location_dest_id","location_dest_id.use_in_transit","location_id","location_id.use_in_transit")
    def verify_op_sunat_transito(self):
        for i in self:
            if i.location_dest_id.use_in_transit or i.location_id.use_in_transit:
                i.op_sunat_transito = True
            else:
                i.op_sunat_transito = False





    def button_validate(self):
        t = super(stock_picking,self).button_validate()
        for i in self:
            if i.location_dest_id.use_in_transit and i.state=="done":
                type_operation = self.env["stock.picking.type"].sudo().search([("usar_en_recepciondetransito","=",True),("default_location_src_id","=",i.location_dest_id.id),("company_id","in",[i.env.company.id,False])])
                if len(type_operation)>1:
                    raise UserError("Multiples Tipos de Operación con ubicacion origen de transito a almacen")
                if len(type_operation)==0:
                    raise UserError("No se Encontro un Tipo de Operación con ubicacion origen de transito a almacen")
                vls_create={
                    "partner_id":i.partner_id.id,
                    "origin":i.name,
                    "company_id":i.company_id.id,
                    "picking_type_id":type_operation.id,
                    "location_id":type_operation.default_location_src_id.id,
                    "location_dest_id":type_operation.default_location_dest_id.id,
                    "origin_transit_id":i.id,
                    "state":"draft"
                }
                pick_destino = self.env["stock.picking"].sudo().create(vls_create)

                for lin in i.move_ids_without_package:
                    vls_move = {
                        "product_id":lin.product_id.id,
                        "name":lin.name,
                        #"product_packaging_id":lin.product_packaging_id.id,
                        "product_uom_qty":lin.product_uom_qty,
                        "product_uom":lin.product_uom.id,
                        "analytic_account_id":lin.analytic_account_id.id,
                        "analytic_tag_id":lin.analytic_tag_id.id,
                        "picking_id":pick_destino.id,
                        "picking_type_id":type_operation.id,
                        "location_id":type_operation.default_location_src_id.id,
                        "location_dest_id":type_operation.default_location_dest_id.id,
                        "origin_move_id":lin.id,
                        "state":"draft"
                    }
                    self.env["stock.move"].sudo().create(vls_move)
                pick_destino.sudo().action_confirm()
                pick_destino.move_line_ids_without_package.sudo().unlink()
                for sml in i.move_line_ids_without_package:
                    move = self.env["stock.move"].sudo().search([("origin_move_id","=",sml.move_id.id),("picking_id","=",pick_destino.id)])
                    if len(move)!=1:
                        #en teoria nunca deberia pasar
                        raise UserError("No se encontro un movimiento origen")
                    vls_move_line = {
                        "product_id":sml.product_id.id,
                        "move_id":move.id,
                        "picking_id":pick_destino.id,
                        "origin":i.name,
                        "location_id":type_operation.default_location_src_id.id,
                        "location_dest_id":type_operation.default_location_dest_id.id,
                        "qty_done":sml.qty_done,
                        "lot_id":sml.lot_id.id,
                        "lot_name":sml.lot_name if not sml.lot_id.id else False,
                        "product_uom_id":sml.product_uom_id.id,
                    }
                    self.env["stock.move.line"].sudo().create(vls_move_line)
        return t




