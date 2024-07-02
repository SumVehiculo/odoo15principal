from odoo import models, fields, api

class GeneralWorkOrderReportTotal(models.Model):
    _name="general.work.order.report.total"
    _description="Reporte General de Orden de Trabajo" 
    
    
    
    
    project_id = fields.Many2one('project.project', string='OT')
    client_id = fields.Many2one('res.partner', string='Cliente OT')
    create_date = fields.Date('Fecha')
    start_date = fields.Date('Fecha Inicio del Proyecto')
    end_date = fields.Date('Fecha Fin del Proyecto')
    sale_invoices_total = fields.Float('Total de Lineas de Ventas Facturadas')
    expenses_invoices_total = fields.Float('Total de Lineas de Gastos Facturados')
    kardex_total = fields.Float('Total Lineas de Kardex')
    hourly_cost_total = fields.Float('Total Costo Horas')
    net_total = fields.Float('Neto ')
    net_by_sale_total = fields.Float('% Neto/Ventas')
    
    
    
    