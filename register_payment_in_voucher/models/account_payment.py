# -*- coding: utf-8 -*-
from odoo import models, fields, api

class AccountPayment(models.Model):
	_inherit = 'account.payment'

	def _prepare_move_line_default_vals(self, write_off_line_vals=None):
		line_vals_list = super(AccountPayment,self)._prepare_move_line_default_vals(write_off_line_vals = write_off_line_vals)
		for line in line_vals_list:
			if line['account_id'] == self.outstanding_account_id.id:
				line['cash_flow_id'] = self.cash_flow_id.id or None
				line['type_document_id'] = self.type_doc_cash_id.id or None
				line['nro_comp'] = self.cash_nro_comp or None
			if line['account_id'] == self.destination_account_id.id:
				line['type_document_id'] = self.type_document_id.id or None
				line['nro_comp'] = self.nro_comp or None
			line['tc'] = self.type_change if self.currency_id != self.company_id.currency_id else 1 
		return line_vals_list
	
	def _synchronize_to_moves(self, changed_fields):
		res = super(AccountPayment,self)._synchronize_to_moves(changed_fields = changed_fields)
		if self._context.get('skip_account_move_synchronization'):
			return
		if not any(field_name in changed_fields for field_name in (
			 'catalog_payment_id','type_doc_cash_id','cash_nro_comp','type_document_id','nro_comp','type_change','ref'
		)):
			return
		for pay in self.with_context(skip_account_move_synchronization=True):
			liquidity_lines, counterpart_lines, writeoff_lines = pay._seek_for_lines()
			pay.move_id.write({
				'td_payment_id': pay.catalog_payment_id.id or None,
				'currency_rate': pay.type_change,
				'ref': pay.cash_nro_comp,
				'glosa':pay.ref
			})
			counterpart_lines.write({
				'type_document_id': pay.type_document_id.id or None,
				'nro_comp': pay.nro_comp or None
			})
			liquidity_lines.write({
				'type_document_id': pay.type_doc_cash_id.id or None,
				'nro_comp': pay.cash_nro_comp or None
			})

		return res
	
	def action_post(self):
		super(AccountPayment,self).action_post()
		self.move_id.td_payment_id = self.catalog_payment_id.id or None
		self.move_id.ref = self.cash_nro_comp
		self.move_id.glosa = self.ref
		if self.currency_id.id != self.company_id.currency_id.id:
			self.move_id.currency_rate = self.type_change
			self.paired_internal_transfer_payment_id.move_id.currency_rate = self.type_change

class AccountPaymentRegister(models.TransientModel):
	_inherit = 'account.payment.register'

	def _create_payment_vals_from_wizard(self):
		payment_vals = super(AccountPaymentRegister,self)._create_payment_vals_from_wizard()
		payment_vals['type_document_id'] = self.type_document_id.id
		payment_vals['nro_comp'] = self.nro_comp
		payment_vals['cash_flow_id'] = self.cash_flow_id.id
		payment_vals['catalog_payment_id'] = self.catalog_payment_id.id
		payment_vals['type_doc_cash_id'] = self.type_doc_cash_id.id
		payment_vals['cash_nro_comp'] = self.cash_nro_comp
		payment_vals['is_personalized_change'] = self.is_personalized_change
		payment_vals['type_change'] = self.type_change
		payment_vals['manual_batch_payment_id'] = self.manual_batch_payment_id.id
		return payment_vals