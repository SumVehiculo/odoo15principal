# -*- coding: utf-8 -*-
from odoo import models, fields, api, _ 
from odoo.exceptions import UserError, ValidationError

class AccountMove(models.Model):
	_inherit = 'account.move'

	@api.model
	def search(self, args, offset=0, limit=None, order=None, count=False):		
		if self.env.user.has_group("account_restrict_invoice_cash.group_invoice_only"):
			args = [('create_uid', '=', self.env.user.id)] + args
		t = super(AccountMove, self).search(args, offset, limit, order, count=count)		
		return t

		


class account_bank_statement(models.Model):
	_inherit = 'account.bank.statement'

	@api.model
	def search(self, args, offset=0, limit=None, order=None, count=False):
		if self.env.user.has_group("account_restrict_invoice_cash.group_invoice_only"):
			opt = 0
			for condition in args:
				if isinstance(condition,list)and len(condition)==3:					
					field, operator, value = condition					
					#['&', ['journal_id.type', '=', 'cash'], ['journal_id.check_surrender', '=', False]]
					if field ==	'journal_id.type' and operator == '=' and value == 'cash':		
						opt+= 1
					elif field ==	'journal_id.check_surrender' and operator == '=' and value == False:
						opt+= 1
			if opt==2:
				args = [('create_uid', '=', self.env.user.id)] + args
		t = super(account_bank_statement, self).search(args, offset, limit, order, count=count)		
		return t

		