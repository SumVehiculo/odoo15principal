# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError

class HrPayslipRun(models.Model):
	_inherit = 'hr.payslip.run'

	def vouchers_by_lot(self):
		if len(self.ids) > 1:
			raise UserError('No se puede seleccionar mas de un registro para este proceso')
		return self.env['hr.payslip'].get_vouchers(self.slip_ids)