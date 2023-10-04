# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class AccountMove(models.Model):
	_inherit = 'account.move'

	move_free_transfer_id = fields.Many2one('account.move',string=u'Asiento de Transferencia Gratuita',copy=False)

	def button_cancel(self):
		if self.move_free_transfer_id.id:
			if self.move_free_transfer_id.state != 'draft':
				for mm in self.move_free_transfer_id.line_ids:
					mm.remove_move_reconcile()
				self.move_free_transfer_id.button_cancel()
			self.move_free_transfer_id.line_ids.unlink()
			self.move_free_transfer_id.name = "/"
			self.move_free_transfer_id.unlink()
		return super(AccountMove,self).button_cancel()

	def button_draft(self):
		if self.move_free_transfer_id.id:
			if self.move_free_transfer_id.state != 'draft':
				for mm in self.move_free_transfer_id.line_ids:
					mm.remove_move_reconcile()
				self.move_free_transfer_id.button_cancel()
			self.move_free_transfer_id.line_ids.unlink()
			self.move_free_transfer_id.name = "/"
			self.move_free_transfer_id.unlink()
		return super(AccountMove,self).button_draft()

	def action_post(self):
		res = super(AccountMove,self).action_post()
		for move in self:
			if move.move_type == 'out_invoice':
				free_transer_tax_ids = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).free_transer_tax_ids
				if free_transer_tax_ids:
					is_free = False
					lines = []
					for tax_free in free_transer_tax_ids:
						for line in move.line_ids:
							if tax_free.id in line.tax_ids.ids:
								lines.append(line)
								is_free = True
					if is_free:
						move.make_move_free_transfer(lines)
		return res


	def make_move_free_transfer(self,lines):
		m = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1)
		if not m.free_transfer_journal_id.id:
			raise UserError(u"No esta configurado el Diario de Transferencias Gratuitas en Parametros Principales de Contabilidad para su Compañía, es necesario si usa el impuesto de Transferencias Gratuitas.")
		if not m.free_transer_account_id.id:
			raise UserError(u"No esta configurado la Cuenta de Transferencias Gratuitas en Parametros Principales de Contabilidad para su Compañía, es necesario si usa el impuesto de Transferencias Gratuitas.")
		
		
		data = {
			'journal_id': m.free_transfer_journal_id.id,
			'ref':(self.ref if self.ref else 'Borrador'),
			'date': self.date,
			'invoice_date': self.invoice_date,
			'company_id': self.company_id.id,
			'glosa': 'EXTORNO POR TRANSFERENCIA GRATUITA',
			'currency_rate': self.currency_rate,
			'move_type': 'entry'
		}

		move_lines = []
		debit = credit = amount_currency = 0

		for line in lines:
			values = (0,0,{
					'account_id': line.account_id.id,
					'debit': line.credit,
					'credit':line.debit,
					'name':'EXTORNO POR TRANSFERENCIA GRATUITA',
					'partner_id': line.partner_id.id,
					'nro_comp': line.nro_comp,
					'type_document_id': line.type_document_id.id,
					'currency_id': line.currency_id.id if line.currency_id else None,
					'amount_currency': line.amount_currency*-1 if line.amount_currency else None,
					'tc': line.tc,
					'company_id': self.company_id.id,			
					})
			move_lines.append(values)
			debit += line.credit
			credit += line.debit
			amount_currency += line.amount_currency
		free_tax_names = []
		for tax_free in m.free_transer_tax_ids:
			free_tax_names.append(tax_free.name)

		tax_lines = self.line_ids.filtered(lambda l: l.name in free_tax_names)

		for tax_line in tax_lines:
			values = (0,0,{
						'account_id': m.free_transer_account_id.id,
						'debit': tax_line.credit,
						'credit':tax_line.debit,
						'name':'EXTORNO POR TRANSFERENCIA GRATUITA',
						'partner_id': tax_line.partner_id.id,
						'nro_comp': tax_line.nro_comp,
						'type_document_id': tax_line.type_document_id.id,
						'currency_id': tax_line.currency_id.id if tax_line.currency_id else None,
						'amount_currency': tax_line.amount_currency*-1 if tax_line.amount_currency else 0,
						'tc': tax_line.tc,
						'company_id': self.company_id.id,			
						})
			move_lines.append(values)
			debit += tax_line.credit
			credit += tax_line.debit
			amount_currency += tax_line.amount_currency

		filtered_line = self.line_ids.filtered(lambda l: l.account_id.internal_type in ['receivable','payable'])
		values = (0,0,{
					'account_id': filtered_line.account_id.id,
					'debit':credit,
					'credit':debit,
					'name':'EXTORNO POR TRANSFERENCIA GRATUITA',
					'partner_id': filtered_line.partner_id.id,
					'nro_comp': filtered_line.nro_comp,
					'type_document_id': filtered_line.type_document_id.id,
					'currency_id': filtered_line.currency_id.id if filtered_line.currency_id else None,
					'amount_currency': amount_currency if filtered_line.currency_id else 0,
					'tc': filtered_line.tc,
					'company_id': self.company_id.id,
					})
		move_lines.append(values)

		data['line_ids'] = move_lines
		tt = self.env['account.move'].create(data)
		ids_conciliation = []
		ids_conciliation.append(filtered_line.id)

		for line in tt.line_ids:
			if line.account_id == filtered_line.account_id and line.nro_comp == filtered_line.nro_comp and line.type_document_id == filtered_line.type_document_id and line.partner_id.id == filtered_line.partner_id.id:
				ids_conciliation.append(line.id)
		
		if tt.state =='draft':
			tt.post()

		if len(ids_conciliation)>1:
			self.env['account.move.line'].browse(ids_conciliation).reconcile()

		self.move_free_transfer_id = tt.id