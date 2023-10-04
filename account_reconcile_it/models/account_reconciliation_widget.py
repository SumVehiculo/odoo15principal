# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.tools.misc import parse_date

class AccountReconciliation(models.AbstractModel):
	_inherit = 'account.reconciliation.widget'

	@api.model
	def _prepare_move_lines(self, move_lines, target_currency=False, target_date=False, recs_count=0):
		res = super(AccountReconciliation,self)._prepare_move_lines(move_lines,target_currency,target_date,recs_count)
		c=0
		for line in move_lines:
			res[c]['nro_comp'] = 'Sin comprobante'
			c+=1
		return res