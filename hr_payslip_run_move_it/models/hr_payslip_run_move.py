# -*- coding:utf-8 -*-
from odoo import api, fields, models, tools
from odoo.exceptions import UserError

class HrPayslipRunMove(models.Model):
	_name = 'hr.payslip.run.move'
	_description = 'Hr Payslip Run Move'
	_auto = False
	_order = 'sequence'

	salary_rule_id = fields.Many2one('hr.salary.rule', string='Regla Salarial')
	sequence = fields.Integer(string='Secuencia')
	code = fields.Char(related='salary_rule_id.code', string='Codigo')
	description = fields.Char(string='Descripcion')
	analytic_account_id = fields.Many2one('account.analytic.account', string='Cuenta Analitica')
	account_id = fields.Many2one('account.account', string='Cuenta Contable')
	debit = fields.Float(string='Debe')
	credit = fields.Float(string='Haber')
	partner_id = fields.Many2one('res.partner','Socio')

	# def init(self):
	# 	tools.drop_view_if_exists(self.env.cr, self._table)
	# 	self.env.cr.execute('''
	# 		CREATE OR REPLACE VIEW %s AS (
	# 			SELECT row_number() OVER () AS id,
	# 				prm.sequence,
	# 				prm.salary_rule_id,
	# 				null as analytic_account_id,
	# 				prm.account_debit as account_id,
	# 				0 as debit,
	# 				0 as credit
	# 				from payslip_run_move prm limit 1
	#
	# 		)''' % (self._table,)
	# 	)
