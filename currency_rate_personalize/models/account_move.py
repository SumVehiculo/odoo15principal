# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError

class AccountMove(models.Model):
	_inherit = 'account.move'

	@api.onchange('invoice_date','tc_per','currency_rate','currency_id')
	def _onchange_tc_per(self):
		for line in self.line_ids:
			line._onchange_currency()
		if self.tc_per:
			self._recompute_dynamic_lines()

	@api.onchange('invoice_date','tc_per')
	def _get_currency_rate(self):
		if self.tc_per:
			date_currency = self.invoice_date if self.invoice_date else fields.Date.today()
			currency_id = self.env.ref('base.USD') if self.currency_id == self.company_id.currency_id else self.currency_id
			cu_rate = self.env['res.currency.rate'].search([('name','=',date_currency),('currency_id','=',currency_id.id),('company_id','=',self.company_id.id)],limit=1)
			if cu_rate:
				self.currency_rate = cu_rate.sale_type
				if self.is_invoice(include_receipts=True):
					for line in self.line_ids:
						line.tc = cu_rate.sale_type

	@api.onchange('tc_per','date')
	def _get_currency_rate_date(self):
		if not self.tc_per:
			date_currency = self.date if self.date else fields.Date.today()
			currency_id = self.env.ref('base.USD') if self.currency_id == self.company_id.currency_id else self.currency_id
			cu_rate = self.env['res.currency.rate'].search([('name','=',date_currency),('currency_id','=',currency_id.id),('company_id','=',self.company_id.id)],limit=1)
			if cu_rate:
				self.currency_rate = cu_rate.sale_type
				if self.is_invoice(include_receipts=True):
					for line in self.line_ids:
						line.tc = cu_rate.sale_type
	
	def _post(self, soft=True):
		res = super(AccountMove,self)._post(soft=soft)
		for move in self:
			if move.is_invoice(include_receipts=True):
				for line in move.line_ids:
					line.tc = move.currency_rate
		return res

	@api.onchange('line_ids', 'invoice_payment_term_id', 'invoice_date_due', 'invoice_cash_rounding_id', 'invoice_vendor_bill_id')
	def _onchange_recompute_dynamic_lines(self):
		res = super(AccountMove, self)._onchange_recompute_dynamic_lines()
		if self.currency_id != self.env.company.currency_id:
			for line in self.line_ids:
				if self.is_invoice(include_receipts=True):
					line.tc = self.currency_rate
				if self.tc_per:
					if line.debit > 0:
						line.debit = line.amount_currency / (1 / self.currency_rate)
					else:
						line.credit = abs(line.amount_currency) / (1 / self.currency_rate)
		return res

class AccountMoveLine(models.Model):
	_inherit = 'account.move.line'

	@api.onchange('product_id')
	def _onchange_product_id(self):
		res = super(AccountMoveLine, self)._onchange_product_id()
		if self.move_id.tc_per and self.move_id.currency_id != self.env.company.currency_id and self.account_id.user_type_id.type not in ['receivable','payable']:
			for line in self:
				price_unit = self._get_computed_price_unit()
				line.price_unit = price_unit * (1 / self.move_id.currency_rate)
		return res

	@api.onchange('product_uom_id')
	def _onchange_uom_id(self):
		res = super(AccountMoveLine, self)._onchange_uom_id()
		if self.move_id.tc_per and self.move_id.currency_id != self.env.company.currency_id and self.account_id.user_type_id.type not in ['receivable','payable']:
			for line in self:
				price_unit = self._get_computed_price_unit()
				line.price_unit = price_unit * (1 / self.move_id.currency_rate)
		return res

	@api.model
	def _get_fields_onchange_subtotal_model(self, price_subtotal, move_type, currency, company, date):
		res = super(AccountMoveLine, self)._get_fields_onchange_subtotal_model(price_subtotal, move_type, currency, company, date)
		if self.move_id.tc_per and self.move_id.currency_id != self.move_id.company_currency_id:
			if self.account_id.user_type_id.type not in ['receivable','payable']:
				if res['debit'] > 0:
					res['debit'] = res['amount_currency'] / (1 / self.move_id.currency_rate)
				else:
					res['credit'] = abs(res['amount_currency']) / (1 / self.move_id.currency_rate)
			if self.move_id.is_invoice(include_receipts=True):
				self.tc = self.move_id.currency_rate
		return res
	
	@api.onchange('amount_currency')
	def _onchange_amount_currency(self):
		res = super(AccountMoveLine, self)._onchange_amount_currency()
		if self.move_id.tc_per and self.move_id.currency_id != self.env.company.currency_id:
			if self.account_id.user_type_id.type not in ['receivable','payable']:
				if self.debit > 0:
					self.debit = self.amount_currency / (1 / self.move_id.currency_rate)
				else:
					self.credit = abs(self.amount_currency) / (1 / self.move_id.currency_rate)
			if self.move_id.is_invoice(include_receipts=True):
				self.tc = self.move_id.currency_rate
		return res
	
	@api.onchange('tc')
	def _onchange_tc(self):
		for line in self:
			line._onchange_currency()

	def _recompute_debit_credit_from_amount_currency(self):
		for line in self:
			# Recompute the debit/credit based on amount_currency/currency_id and date.

			company_currency = line.account_id.company_id.currency_id
			balance = line.amount_currency
			if line.currency_id and company_currency and line.currency_id != company_currency:
				if line.move_id.tc_per:
					balance = line.amount_currency * line.tc
				else:
					balance = line.currency_id._convert(balance, company_currency, line.account_id.company_id, line.move_id.date or fields.Date.today())
				line.debit = balance > 0 and balance or 0.0
				line.credit = balance < 0 and -balance or 0.0
