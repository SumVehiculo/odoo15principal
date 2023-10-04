# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError

class HrPayslipRun(models.Model):
	_inherit = 'hr.payslip.run'

	def import_advances_by_lot(self):
		return self.slip_ids.import_advances()

	def import_loans_by_lot(self):
		return self.slip_ids.import_loans()