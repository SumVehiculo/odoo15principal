# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class AccountBankStatementLine(models.Model):
	_inherit = 'account.bank.statement.line'

	@api.model
	def _prepare_counterpart_move_line_vals(self, counterpart_vals, move_line=None):
		data = super(AccountBankStatementLine,self)._prepare_counterpart_move_line_vals(counterpart_vals=counterpart_vals,move_line=move_line)
		if move_line:
			data['nro_comp'] = move_line.nro_comp
			data['type_document_id'] = move_line.type_document_id.id
		return data
	
	@api.model
	def _prepare_liquidity_move_line_vals(self):
		data = super(AccountBankStatementLine,self)._prepare_liquidity_move_line_vals()
		data['nro_comp'] = self.ref
		data['type_document_id'] = self.type_document_id.id
		data['cash_flow_id'] = self.account_cash_flow_id.id
		return data
	
	@api.model_create_multi
	def create(self, vals_list):
		st_lines = super(AccountBankStatementLine,self).create(vals_list)
		for st_line in st_lines:
			st_line.move_id.write({'glosa':st_line.payment_ref})
			st_line.move_id.write({'td_payment_id':st_line.catalog_payment_id.id})
		return st_lines
	
	def _synchronize_to_moves(self, changed_fields):
		res = super(AccountBankStatementLine,self)._synchronize_to_moves(changed_fields = changed_fields)
		if self._context.get('skip_account_move_synchronization'):
			return
		if not any(field_name in changed_fields for field_name in (
			 'payment_ref','catalog_payment_id','type_document_id'
		)):
			return
		for st_line in self.with_context(skip_account_move_synchronization=True):
			st_line.move_id.write({
				'td_payment_id': st_line.catalog_payment_id.id or None,
				'glosa': st_line.payment_ref,
				'l10n_latam_document_type_id': st_line.type_document_id.id or None
			})
		return res

class AccountBankStatement(models.Model):
	_inherit = 'account.bank.statement'

	def button_post(self):
		self.write({'balance_end_real': self.balance_end})
		res = super(AccountBankStatement,self).button_post()
		return res
	
	def reg_account_move_lines_it(self):
		for statement in self:
			if not statement.journal_check_surrender:
				raise UserError(u'Solo se aplica en Rendiciones.')
			sql = """update account_move_line set partner_id = %s, type_document_id = (SELECT ID FROM l10n_latam_document_type where code = '00' LIMIT 1), nro_comp = '%s'
					where statement_id = %d and account_id = %d """%(str(statement.employee_id.id) if statement.employee_id else 'null',statement.name,statement.id,statement.journal_id.default_account_id.id)
			self.env.cr.execute(sql)
			
		return self.env['popup.it'].get_message('Se regularizaron correctamente los registros seleccionados.')
	
	def create_journal_entry_surrender(self):
		for statement in self:
			statement.write({'line_ids': [(0,0,{
			'date': statement.date_surrender,
			'payment_ref': statement.memory,
			'partner_id': statement.employee_id.id if statement.employee_id else None,
			'catalog_payment_id':statement.einvoice_catalog_payment_id.id if statement.einvoice_catalog_payment_id else None,
			'amount': statement.amount_surrender,
			'company_id': statement.company_id.id,
		})]})

		return self.env['popup.it'].get_message('Se creó el asiento de entrega.')