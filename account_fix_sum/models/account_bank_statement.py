# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
import re

class AccountBankStatement(models.Model):
	_inherit = 'account.bank.statement'
	
	sequence_number = fields.Char(string='Secuencia')

	@api.model
	def create(self,vals):
		if self.env.context.get('journal_type') == 'cash' and self.env.context.get('default_journal_check_surrender'):
			id_seq = self.env['ir.sequence'].sudo().search([('name','=','Rendiciones Tesoreria'),('company_id','=',self.env.company.id)], limit=1)
			if not id_seq:
				id_seq = self.env['ir.sequence'].sudo().create({'name':'Rendiciones Tesoreria','implementation':'no_gap','active':True,'prefix':'REN-','padding':6,'number_increment':1,'number_next_actual' :1, 'company_id': self.env.company.id})
			sequ = id_seq._next()
			vals['sequence_number'] = sequ		
			vals['name'] = sequ

		t = super(AccountBankStatement,self).create(vals)
		return t