# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class AccountBatchPayment(models.Model):
	_inherit = "account.batch.payment"
	
	@api.constrains('name')
	def check_duplicate_name(self):
		if self.env['account.batch.payment'].search([('name', '=', self.name), ('id', '!=', self.id)]):
			raise UserError('Ya existe un Lote de Pagos con esta referencia')

	def set_draft(self):
		self.state = 'draft'

	#def add_payments(self):
	#	ids = self.env['account.payment'].search([('manual_batch_payment_id', '=', self.id),('payment_type', '=', self.batch_type)]).ids
	#	self.payment_ids = [(6, 0, ids)]