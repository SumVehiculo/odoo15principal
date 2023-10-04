# -*- coding:utf-8 -*-

from odoo import models, fields

class HrPayrollStructureType(models.Model):
    _inherit = 'hr.payroll.structure.type'
    _description = 'Salary Structure Type'

    default_resource_calendar_id = fields.Many2one(default=None)