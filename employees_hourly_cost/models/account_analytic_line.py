from odoo import models, fields, api, _
from odoo.exceptions import UserError

class AccountAnalyticLine(models.Model):
    _inherit="account.analytic.line"
    
    total_cost_per_hour = fields.Float(
        'Costo Total Por Hora', 
        compute="_compute_total_cost_per_hour",
        store=True
    )
    
    def _compute_total_cost_per_hour(self):
        for rec in self:
            related_employee = self.env['hr.employee.hourly.cost'].search([
                ('employee_id','=', rec.employee_id.id)
            ])
            if not related_employee:
                rec.total_cost_per_hour=0.00
                return
            rec.total_cost_per_hour = round(related_employee.cost  * round(rec.unit_amount,2), 2)