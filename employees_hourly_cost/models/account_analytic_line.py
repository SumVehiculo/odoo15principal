from odoo import models, fields, api, _
from odoo.exceptions import UserError

class AccountAnalyticLine(models.Model):
    _inherit="account.analytic.line"
    
    total_cost_per_hour = fields.Float('Costo Total Por Hora', compute="_compute_total_cost_per_hour")
    
    def _compute_total_cost_per_hour(self):
        for rec in self:
            related_employee = self.env['hr.employee.hourly.cost'].search([
                ('employee_id','=', self.employee_id.id)
            ])
            if not related_employee:
                self.total_cost_per_hour=0.00
                return
            self.total_cost_per_hour = related_employee.cost * self.unit_amount