from odoo import models, fields, api, _
from odoo.exceptions import UserError

class WorkOrderReportWizard(models.TransientModel):
    _name="work.order.report.wizard"
    _description="Wizard Reporte Orden de Trabajo"
    
    company_id = fields.Many2one('res.company', string='Compañia')
    work_order_id = fields.Many2one('project.project', string='OT')
    start_name = fields.Date('Desde ')
    end_name = fields.Date('Hasta')
   
    def get_report(self):
        pass
    
    def sale_invoiced_data(self):
        pass
    
    def invoiced_expense_data(self):
        pass
    
    def warehouse_item_date(self):
        pass