# -*- coding:utf-8 -*-
from odoo import api, fields, models, tools
from odoo.exceptions import UserError

class HrPayslipRunMove(models.Model):
	_inherit = 'hr.payslip.run.move'

	analytic_tag_id = fields.Many2one('account.analytic.tag', string='Etiqueta Analitca')
