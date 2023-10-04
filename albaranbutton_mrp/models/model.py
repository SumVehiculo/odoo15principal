from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class stock_balance_report_multipleorigin(models.TransientModel):
    _name = 'stock.balance.report.multipleorigin'
    _description = 'Origenes de reservas'

    name = fields.Char(string="Referencia")
#    location_id = fields.Many2one("stock.location",string="De")
#    location_dest_id = fields.Many2one("stock.location",string="Para")
#    state = fields.Char(string="Estado")
    producto = fields.Many2one("product.product",string="Producto")
    cantidad_pedida=fields.Float(string="Cantidad Pedida")
    cantidad_reservada=fields.Float(string="Cantidad Reservada")
    fabrication_id = fields.Many2one("mrp.production",string="Orden de Producción")
    picking_id = fields.Many2one("stock.picking",string="Albaran")
    lote = fields.Many2one("stock.production.lot",string="Lote")


    def action_get_pick_op(self):
        self.ensure_one()
        if self.fabrication_id.id:
            return {
				'name': 'Órdenes de producción',
				'type': 'ir.actions.act_window',
				'res_model': 'mrp.production',
				'view_mode': 'form',
				'view_type': 'form',
                'res_id':self.fabrication_id.id,
                'view_id':self.env.ref('mrp.mrp_production_form_view').id 
			}
        elif self.picking_id.id:
            return {
				'name': 'Transferencia',
				'type': 'ir.actions.act_window',
				'res_model': 'stock.picking',
				'view_mode': 'form',
				'view_type': 'form',
                'res_id':self.picking_id.id,
                'view_id':self.env.ref('stock.view_picking_form').id 
			}

class alberan_button(models.Model):
    _inherit = 'stock.balance.report'
    # _description = 'model.technical.name'

    def action_name(self):

        self.env.cr.execute(""" 
        select picking_id, 'picking', product_uom_qty,qty_done from stock_move_line 
            where location_id = """ +str(self.almacen_id.id)+ """ and product_id = """ +str(self.product_id.id)+ """ 
            and state in ('partially_available','assigned') and picking_id is not null
        union all
            select sm.raw_material_production_id, 'production',sml.product_uom_qty,sml.qty_done from stock_move_line sml
                inner join stock_move sm on sm.id = sml.move_id
                where sml.location_id = """ +str(self.almacen_id.id)+ """ and sml.product_id = """ +str(self.product_id.id)+ """ 
                and sml.state in ('partially_available','assigned') and sm.raw_material_production_id is not null
        """)
        ids_domain = []
        for x in self.env.cr.fetchall():
            refname=False
            ref_pick_obj=False
            ref_produc_obj=False
            if x[1]=="picking":
                refname = self.env["stock.picking"].sudo().browse(x[0]).name
                ref_pick_obj = x[0]
            elif x[1]=="production":
                ref_produc_obj = x[0]
                refname = self.env["mrp.production"].sudo().browse(x[0]).name
            vals={
                'name':refname,
                'producto':self.product_id.id,
                'cantidad_reservada':x[2],
                'cantidad_pedida': x[3],
                'fabrication_id': ref_produc_obj,
                'picking_id': ref_pick_obj
            }
            nuveo = self.env["stock.balance.report.multipleorigin"].sudo().create(vals)
            ids_domain.append(nuveo.id)
        nombre = "Movimientos de " + self.producto.name_get()[0][1]
        if len(ids_domain)==0:
            raise UserError("Producto no tiene movimientos de reservas")
        return {
            'name': nombre,
            'res_model': 'stock.balance.report.multipleorigin',
            'view_mode': 'tree',
            'view_type': 'form',
            'view_id':self.env.ref('albaranbutton_mrp.insumostree_nolote').id,
            # 'context': "{'name':'cemento'}",
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': [('id', 'in', ids_domain)]
            # 'domain':
        }

class StockBalanceReportLote(models.Model):
    _inherit = 'stock.balance.report.lote'


    def action_name(self):

        self.env.cr.execute(""" 
        select sml.picking_id, 'picking', sml.product_uom_qty,sml.qty_done from stock_move_line sml 
        inner join stock_production_lot on stock_production_lot.id = sml.lot_id 
        where stock_production_lot.id """ + ((" = " + str(self.lote.id) ) if self.lote else " is null " ) 
        +  """ and sml.location_id = """ +str(self.almacen_id.id)+ """ 
        and sml.product_id = """ +str(self.product_id.id)+ """ 
        and sml.state in ('partially_available','assigned') and sml.picking_id is not null 
        
        union all
            select sm.raw_material_production_id, 'production',sml.product_uom_qty,sml.qty_done from stock_move_line sml
                inner join stock_move sm on sm.id = sml.move_id
                inner join stock_production_lot on stock_production_lot.id = sml.lot_id 
                where stock_production_lot.id """ + ((" = " + str(self.lote.id) ) if self.lote else " is null " )+""" 
                and sml.location_id = """ +str(self.almacen_id.id)+ """ and sml.product_id = """ +str(self.product_id.id)+ """ 
                and sml.state in ('partially_available','assigned') and sm.raw_material_production_id is not null
        """)
        ids_domain = []
        for x in self.env.cr.fetchall():
            refname=False
            ref_pick_obj=False
            ref_produc_obj=False
            if x[1]=="picking":
                refname = self.env["stock.picking"].sudo().browse(x[0]).name
                ref_pick_obj = x[0]
            elif x[1]=="production":
                ref_produc_obj = x[0]
                refname = self.env["mrp.production"].sudo().browse(x[0]).name
            vals={
                'name':refname,
                'producto':self.product_id.id,
                'cantidad_reservada':x[2],
                'cantidad_pedida': x[3],
                'fabrication_id': ref_produc_obj,
                'picking_id': ref_pick_obj,
                'lote':self.lote.id
            }
            nuveo = self.env["stock.balance.report.multipleorigin"].sudo().create(vals)
            ids_domain.append(nuveo.id)
        nombre = "Movimientos de " + self.producto.name_get()[0][1]
        if len(ids_domain)==0:
            raise UserError("Producto no tiene movimientos de reservas")
        return {
            'name': nombre,
            'res_model': 'stock.balance.report.multipleorigin',
            'view_mode': 'tree',
            'view_type': 'form',
            'view_id':self.env.ref('albaranbutton_mrp.insumostree').id,
            # 'context': "{'name':'cemento'}",
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': [('id', 'in', ids_domain)]
            # 'domain':
        }