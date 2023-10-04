# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class AccountBankStatement(models.Model):
	_inherit = 'account.bank.statement'

	employee_en_id = fields.Many2one('hr.employee', string='Responsable')
	check_approve = fields.Boolean('Aprobado',default=False,tracking=True)
	on_limit = fields.Boolean('Aplica Limite',default=False,tracking=True)

	def get_approve(self):
		for i in self:
			i.check_approve=True
	
	@api.model
	def create(self, vals):
		res = super(AccountBankStatement,self).create(vals)
		for i in res:
			if i.line_ids:
				i.line_ids.onchange_amount()
		return res
	def write(self, vals):
		res = super(AccountBankStatement,self).write(vals)
		for i in self:
			if i.line_ids:
				i.line_ids.onchange_amount()
		return res
class AccountBankStatementLine(models.Model):
	_inherit = 'account.bank.statement.line'


	@api.onchange('amount')
	def onchange_amount(self):
		for i in self:
			if i.statement_id.journal_id:
				if i.statement_id.on_limit==True and i.statement_id.journal_id.amount_max>0 and i.statement_id.journal_type=='cash':
					if i.amount > i.statement_id.journal_id.amount_max:
						raise UserError("NO SE PERMITE GASTOS MAYORES A %s"%(str(i.statement_id.journal_id.amount_max)))
