# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import formatLang, format_date, get_lang


class AccountMove(models.Model):
	_inherit = 'account.move'

	def _check_journal_period_close(self,vals=None):
		for move in self:
			period = self.env['account.journal.period'].search([('company_id','=',move.company_id.id),('date_start','<=',move.date),('date_end','>=',move.date)],limit=1)
			if period:
				if period.state == 'done':
					raise UserError('No puede agregar/modificar entradas anteriores e inclusive a la fecha de bloqueo %s - %s. \n %s'%(period.date_start.strftime('%Y/%m/%d'),period.date_end.strftime('%Y/%m/%d'),str(vals if vals else '')))
				else:
					for line in period.line_ids:
						if line.journal_id == move.journal_id and line.state == 'done':
							raise UserError('No puede agregar/modificar entradas del diario "%s" anteriores e inclusive a la fecha de bloqueo %s - %s.\n %s'%(line.journal_id.name,period.date_start.strftime('%Y/%m/%d'),period.date_end.strftime('%Y/%m/%d'),str(vals if vals else '')))
		return True

	def write(self, vals):
		res = True
		for move in self:
			if 'access_token' in vals or 'amount_untaxed' in vals or 'amount_tax' in vals or 'amount_total' in vals or 'amount_residual' in vals or 'amount_untaxed_signed' in vals or 'amount_tax_signed' in vals or 'amount_total_signed' in vals or 'amount_residual_signed' in vals or 'payment_state' in vals:
				res |= super(AccountMove, move).write(vals)
			else:
				if vals:
					move._check_journal_period_close(vals)
				res |= super(AccountMove, move).write(vals)
		return res
			
	@api.model_create_multi
	def create(self, vals_list):
		rslt = super(AccountMove, self).create(vals_list)
		rslt._check_journal_period_close()
		return rslt

	def unlink(self):
		self._check_journal_period_close()
		res = super(AccountMove, self).unlink()
		return res

class AccountMoveLine(models.Model):
	_inherit = 'account.move.line'

	@api.model_create_multi
	def create(self, vals_list):
		res = super(AccountMoveLine, self).create(vals_list)
		moves = res.mapped('move_id')
		moves._check_journal_period_close()
		return res

	def write(self, vals):
		result = True
		for line in self:
			if 'full_reconcile_id' in vals or 'reconciled' in vals or 'amount_residual' in vals or 'amount_residual_currency' in vals:
				result |= super(AccountMoveLine, line).write(vals)
			else:
				if vals:
					line.move_id._check_journal_period_close(vals)
				result |= super(AccountMoveLine, line).write(vals)

		return result

	def unlink(self):
		moves = self.mapped('move_id')
		moves._check_journal_period_close()
		res = super(AccountMoveLine, self).unlink()
		return res