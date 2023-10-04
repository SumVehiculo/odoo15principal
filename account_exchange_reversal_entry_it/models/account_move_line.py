# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class AccountMoveLine(models.Model):
	_inherit = 'account.move.line'
	
	def _create_exchange_difference_move(self):
		exchange_move = super(AccountMoveLine,self)._create_exchange_difference_move()
		if exchange_move:
			if exchange_move.line_ids:
				for c,line in enumerate(exchange_move.line_ids):
					line.type_document_id = self[c-1].type_document_id.id if c-1 < len(self) else None
					line.nro_comp = self[c-1].nro_comp if c-1 < len(self) else None

		return exchange_move
	
	def copy_data(self, default=None):
		res = super(AccountMoveLine, self).copy_data(default=default)
		for line, values in zip(self, res):
			if not line.move_id.is_invoice():
				values['type_document_id'] = line.type_document_id.id
				values['nro_comp'] = line.nro_comp
			if self._context.get('include_business_fields'):
				line._copy_data_extend_business_fields(values)
		return res