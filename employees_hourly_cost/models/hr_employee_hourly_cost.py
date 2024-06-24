from odoo import models, fields, api, _
from odoo.exceptions import UserError

class HrEmployeeHourlyCost(models.Model):
    _name = "hr.employee.hourly.cost"
    _description = "Costo por hora por Empleado"
    _inherit=['mail.thread']
    
    name = fields.Char('Nombre',related='employee_id.name')
    employee_id = fields.Many2one('hr.employee', string='Empleado',tracking=1, required=True)
    cost = fields.Float('Costo Por Hora', tracking=1)
    
    @api.model
    def create(self, vals):
        similar_employees=self.env['hr.employee.hourly.cost'].search([
            ('employee_id','=',vals.get('employee_id'))
        ])
        if similar_employees:
            raise UserError(f"Un registro con este Empleado ya existe")
        return super().create(vals)