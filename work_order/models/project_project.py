from odoo   import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime

class ProjectProject(models.Model):
    _inherit="project.project"
    

    project_name = fields.Char('Nombre del Proyecto')
    
    pick_count = fields.Integer(
        'Contador de Transferencias', 
        compute="_compute_pick_count"
    )
    pick_ids = fields.Many2many('stock.picking', string='Transferencias')
    
    invoice_ids = fields.Many2many(
        'account.move', 
        string='Facturas Relacionadas',
        compute="_compute_invoice_ids"
    )
    
    sale_invoice_count = fields.Integer(
        'Contador de Facturas de Venta', 
    )
    
    purchase_invoice_count = fields.Integer(
        'Contador de Facturas de Compra', 
    )
    
    @api.model
    def create(self, vals):
        actual_month = str(datetime.today().month)
        date = str(datetime.today().year) + '-'
        if len(actual_month) == 1:
            # En caso el mes solo tenga un digito 
            date += '0' + actual_month
        elif len(actual_month) == 2:
            # En caso el mes tenga dos digitos
            date += actual_month
        # date = year+month
        id_seq = self.env['ir.sequence'].sudo().search([
            ('name','=','Correlativo OT SUMVEHICULOS'+date),
            ('company_id','=',self.env.company.id)
        ], limit=1)
        if not id_seq:
            id_seq = self.env['ir.sequence'].sudo().create({
                'name': 'Correlativo OT SUMVEHICULOS'+date,
                'company_id': self.env.company.id,
                'implementation': 'no_gap',
                'active': True,
                'prefix': 'OT',
                'padding': 5,
                'number_increment': 1,
                'number_next_actual': 1
            })
        vals['name'] = id_seq._next()
        return super().create(vals)

    def _compute_pick_count(self):
        for rec in self:
            stock_moves=self.env['stock.move'].sudo().search([
                ('work_order_id','=',rec.id)
            ])
            if not stock_moves:
                rec.pick_count=0
                rec.pick_ids=False
                continue
            rec.pick_count=len(stock_moves)
            rec.pick_ids=stock_moves.picking_id.ids
    
    def _compute_invoice_ids(self):
        for rec in self:
            account_lines=self.env['account.move.line'].sudo().search([
                ('work_order_id','=',rec.id)
            ])
            if not account_lines:
                rec.sale_invoice_count=0
                rec.purchase_invoice_count=0
                continue
            
            rec.sale_invoice_count=len(
                account_lines.filtered(
                    lambda m: m.sale_line_ids != False
                ).move_id.ids
            )
            rec.purchase_invoice_count=len(
                account_lines.filtered(
                    lambda m: m.purchase_line_id != False
                ).move_id.ids
            )
            rec.invoice_ids= account_lines.move_id.ids
    
    
    def action_open_order_picks(self):
        for rec in self: 
            try:
                tree_id = self.env.ref("prorratear_en.stock_picking_fec_tree").id
                form_id = self.env.ref("stock.view_picking_form").id
            except:
                tree_id = False
                form_id = False
            return {
                'name':'Transferencias',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'views': [(tree_id, 'tree'), (form_id, 'form')],
                'res_model': 'stock.picking',
                'type': 'ir.actions.act_window',
                'target': 'current',
                'domain': [
                    ('id','in',rec.pick_ids.ids)
                ]
            }

    def action_open_order_sale_invoices(self):
        for rec in self:
            try:
                tree_id = self.env.ref("account.view_out_invoice_tree").id
                form_id = self.env.ref("account.view_move_form").id
            except:
                tree_id = False
                form_id = False
                
            account_lines=self.env['account.move.line'].sudo().search([
                ('work_order_id', '=', rec.id),
                ('purchase_line_id', '!=', False)
            ])
            
            return {
                'name':'Facturas de Venta',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'views': [(tree_id, 'tree'), (form_id, 'form')],
                'res_model': 'account.move',
                'type': 'ir.actions.act_window',
                'target': 'current',
                'domain': [
                    (
                        'id', 
                        'in', 
                        account_lines.move_id.ids
                    )
                ]
            }

    def action_open_order_purchase_invoices(self):
        for rec in self:
            try:
                tree_id = self.env.ref("account.view_out_invoice_tree").id
                form_id = self.env.ref("account.view_move_form").id
            except:
                tree_id = False
                form_id = False
            
            account_lines=self.env['account.move.line'].sudo().search([
                ('work_order_id', '=', rec.id),
                ('purchase_line_id', '!=', False)
            ])
            return {
                'name':'Facturas de Compra',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'views': [(tree_id, 'tree'), (form_id, 'form')],
                'res_model': 'stock.picking',
                'type': 'ir.actions.act_window',
                'target': 'current',
                'domain': [
                    (
                        'id',
                        'in',
                        account_lines.move_id.ids
                    )
                ]
            }