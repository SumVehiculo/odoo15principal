from odoo   import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime

class ProjectProject(models.Model):
    _inherit="project.project"
    

    project_name = fields.Char('Nombre del Proyecto')
    requested_period_id = fields.Many2one('account.period', string='Solicitado para mes de')
    schedule_date = fields.Date('Fecha de Programación')
    report_delivery_date = fields.Date('Fecha de Entrega de Informes')
    
    pick_count = fields.Integer(
        'Contador de Transferencias', 
        compute="_compute_pick_count"
    )
    pick_ids = fields.Many2many('stock.picking', string='Transferencias')
    sale_invoice_count = fields.Integer(
        'Contador de Facturas de Venta', 
        compute="_compute_sale_invoice_count"
    )
    purchase_invoice_count = fields.Integer(
        'Contador de Facturas de Compra', 
        compute="_compute_purchase_invoice_count"
    )
    estimated_usd_billings = fields.Float('Facturación Estimada USD')

    invoice_date = fields.Date('Fecha de Facturación', compute="_compute_invoice_date",store=True)
    
    @api.depends('sale_invoice_count')
    def _compute_invoice_date(self):
        for project in self:
            account_line=self.env['account.move.line'].sudo().search([
                ('work_order_id', '=', project.id),
                ('sale_line_ids', '!=', False)
            ])
            if not account_line:
                project.invoice_date = False
                continue
            first_account_move = min(account_line.move_id,key=lambda move:move.invoice_date)
            project.invoice_date = first_account_move.invoice_date


    @api.model
    def create(self, vals):
        id_seq = self.env['ir.sequence'].sudo().search([
            ('name','=','Correlativo PROYECTOS'),
            ('company_id','=',self.env.company.id)
        ], limit=1)
        if not id_seq:
            id_seq = self.env['ir.sequence'].sudo().create({
                'name': 'Correlativo PROYECTOS',
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
    
    def _compute_sale_invoice_count(self):
        for rec in self:
            account_lines=self.env['account.move.line'].sudo().search([
                ('work_order_id', '=', rec.id),
                ('sale_line_ids', '!=', False)
            ])
            rec.sale_invoice_count = len(account_lines.move_id.ids)
            
    def _compute_purchase_invoice_count(self):
        for rec in self:
            account_lines=self.env['account.move.line'].sudo().search([
                ('work_order_id', '=', rec.id),
                ('purchase_line_id', '!=', False)
            ])
            rec.purchase_invoice_count = len(account_lines.move_id.ids)
    
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
                ('sale_line_ids', '!=', False)
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