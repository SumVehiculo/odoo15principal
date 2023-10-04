# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
	
class AccountBankStatement(models.Model):
	_inherit = 'account.bank.statement'

	@api.model
	def _default_journal(self):
		journal_type = self.env.context.get('journal_type', False)
		journal_check_surrender = self.env.context.get('default_journal_check_surrender', False)
		company_id = self.env.company.id
		if journal_type:
			if journal_check_surrender:
				return self.env['account.journal'].search([
				('type', '=', journal_type),
				('check_surrender','=', journal_check_surrender),
				('company_id', '=', company_id)
			], limit=1)
			return self.env['account.journal'].search([
				('type', '=', journal_type),
				('company_id', '=', company_id)
			], limit=1)
		return self.env['account.journal']
	
	journal_id = fields.Many2one('account.journal', string='Journal', required=True, states={'confirm': [('readonly', True)]}, default=_default_journal, check_company=True)