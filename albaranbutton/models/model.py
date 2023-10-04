from odoo import models, fields, api
from odoo.exceptions import ValidationError


class alberan_button(models.Model):
    _inherit = 'stock.balance.report'
    # _description = 'model.technical.name'

    def action_name(self):

        self.env.cr.execute(""" select distinct picking_id from stock_move_line where location_id = """ +str(self.almacen_id.id)+ """ and product_id = """ +str(self.product_id.id)+ """ and state in ('partially_available','assigned') """)
        
        ids_domain = []
        for x in self.env.cr.fetchall():
            ids_domain.append(x[0])

        nombre = "Albaranes de " + self.producto.name_get()[0][1]
        return {
            'name': nombre,
            'res_model': 'stock.picking',
            'view_mode': 'tree,form',
            'view_type': 'form',
            # 'views': [(self.env.ref('warehouse.insumo_action').id, 'tree')],
            # 'context': "{'name':'cemento'}",
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': [('id', 'in', ids_domain)]
            # 'domain':
        }

    def action_so_name(self):

        self.env.cr.execute(""" select distinct sale_id from stock_move_line sml inner join stock_picking sp on sp.id = sml.picking_id where sml.location_id = """ +str(self.almacen_id.id)+ """ and sml.product_id = """ +str(self.product_id.id)+ """ and sml.state in ('partially_available','assigned') """)
        
        ids_domain = []
        for x in self.env.cr.fetchall():
            ids_domain.append(x[0])

        nombre = "SO de " + self.producto.name_get()[0][1]
        return {
            'name': nombre,
            'res_model': 'sale.order',
            'view_mode': 'tree,form',
            'view_type': 'form',
            # 'views': [(self.env.ref('warehouse.insumo_action').id, 'tree')],
            # 'context': "{'name':'cemento'}",
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': [('id', 'in', ids_domain)]
            # 'domain':
        }


class StockBalanceReportLote(models.Model):
    _inherit = 'stock.balance.report.lote'


    def action_name(self):

        self.env.cr.execute(""" select distinct picking_id from stock_move_line inner join stock_production_lot on stock_production_lot.id = stock_move_line.lot_id where stock_production_lot.id """ + ((" = " + str(self.lote.id) ) if self.lote else " is null " ) +  """ and stock_move_line.location_id = """ +str(self.almacen_id.id)+ """ and stock_move_line.product_id = """ +str(self.product_id.id)+ """ and stock_move_line.state in ('partially_available','assigned') """)
        
        ids_domain = []
        for x in self.env.cr.fetchall():
            ids_domain.append(x[0])

        nombre = "Albaranes de " + self.producto.name_get()[0][1]
        return {
            'name': nombre,
            'res_model': 'stock.picking',
            'view_mode': 'tree,form',
            'view_type': 'form',
            # 'views': [(self.env.ref('warehouse.insumo_action').id, 'tree')],
            # 'context': "{'name':'cemento'}",
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': [('id', 'in', ids_domain)]
            # 'domain':
        }

    def action_so_name(self):

        self.env.cr.execute(""" select distinct sale_id from stock_move_line sml  inner join stock_production_lot on stock_production_lot.id = sml.lot_id inner join stock_picking sp on sp.id = sml.picking_id where stock_production_lot.id  """ + ((" = " + str(self.lote.id) ) if self.lote else " is null " ) +  """ and sml.location_id = """ +str(self.almacen_id.id)+ """ and sml.product_id = """ +str(self.product_id.id)+ """ and sml.state in ('partially_available','assigned') """)
        
        ids_domain = []
        for x in self.env.cr.fetchall():
            ids_domain.append(x[0])

        nombre = "SO de " + self.producto.name_get()[0][1]
        return {
            'name': nombre,
            'res_model': 'sale.order',
            'view_mode': 'tree,form',
            'view_type': 'form',
            # 'views': [(self.env.ref('warehouse.insumo_action').id, 'tree')],
            # 'context': "{'name':'cemento'}",
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': [('id', 'in', ids_domain)]
            # 'domain':
        }