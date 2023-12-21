# -*- coding: utf-8 -*-
from odoo import models, fields, api, _ 
from odoo.exceptions import UserError, ValidationError

class AccountMove(models.Model):
	_inherit = 'account.move'

	@api.model
	def search(self, args, offset=0, limit=None, order=None, count=False):
		user = self.env.user		
		t = super(AccountMove, self).search(args, offset, limit, order, count=count)
		bu = user.has_group('account_restrict_invoice_cash.group_invoice_only')
		if any(move.move_type in ["in_invoice"] for move in t) and bu:
			args = [('create_uid', '=', self.env.user.id)] + args		
		return t


	@api.model
	def name_search(self, name, args=None, operator='ilike', limit=100):
		args = args or []
		recs = self.browse()
		if name:
			recs = self.search([('create_uid','=', self.env.user.id),
			('name',operator,name)] + args, limit=limit)
		else:
			recs = self.search([] + args, limit=limit)
		return recs.name_get()