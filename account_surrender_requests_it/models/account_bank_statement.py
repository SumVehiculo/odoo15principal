# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class AccountBankStatement(models.Model):
	_inherit = 'account.bank.statement'

	saldo_final = fields.Float(string='Saldo Final',compute='compute_saldo_final',store=True)

	@api.depends('state','line_ids')
	def compute_saldo_final(self):
		for statement in self:
			amount = 0
			for line in statement.line_ids:
				amount += line.amount
			statement.saldo_final = amount

	@api.model
	def create(self,vals):
		journal = self.env['account.journal'].browse(vals['journal_id'])
		if journal.type == 'cash' and journal.check_surrender:
			id_seq = self.env['ir.sequence'].search([('name','=','Rendiciones'),('company_id','=',self.env.company.id)], limit=1)
			if not id_seq:
				id_seq = self.env['ir.sequence'].create({'name':'Rendiciones','implementation':'no_gap','active':True,'prefix':'REN-','padding':6,'number_increment':1,'number_next_actual' :1, 'company_id': self.env.company.id})
			sequ = id_seq._next()	
			vals['name'] = sequ

		t = super(AccountBankStatement,self).create(vals)
		return t
	
	def unlink(self):
		if not self.user_has_groups('account_menu_rendiciones_it.group_bank_statement_group_manager'):
			raise UserError("Usted no puede eliminar el registro si no tiene el permiso 'Extractos Bancarios Admin'.")
		return super(AccountBankStatement, self).unlink()
	