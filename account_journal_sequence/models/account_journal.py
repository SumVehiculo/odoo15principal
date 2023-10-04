# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class AccountJournal(models.Model):
	_inherit = 'account.journal'

	def generar_wizard(self):
		wizard = self.env['sequence.wizard'].create({'name':'Generar Secuencia','journal_id':self.id})
		return {
			'res_id':wizard.id,
			'view_type':'form',
			'view_mode':'form',
			'res_model':'sequence.wizard',
			'views':[[self.env.ref('account_journal_sequence.sequence_wizard_view').id,'form']],
			'type':'ir.actions.act_window',
			'target':'new'
		}

	#@api.model
	#def create(self, vals):
	#	if not vals.get('sequence_id_it'):
	#		vals.update({'sequence_id_it': self.sudo()._create_sequence(vals).id})
	#	journal = super(AccountJournal, self.with_context(mail_create_nolog=True)).create(vals)
	#	return journal
	
	@api.model
	def _get_sequence_prefix(self, code):
		prefix = code.upper()
		return prefix + '/%(range_year)s/'

	@api.model
	def _create_sequence(self, vals=None):
		prefix = self._get_sequence_prefix(vals['code'] if vals else self.code)
		seq_name = vals['code'] if vals else self.code
		seq = {
			'name': '%s Secuencia' % seq_name,
			'implementation': 'no_gap',
			'prefix': prefix,
			'padding': 4,
			'number_increment': 1,
			'use_date_range': True,
		}
		if vals:
			if 'company_id' in vals:
				seq['company_id'] = vals['company_id']
		else:
			seq['company_id'] = self.company_id.id
		seq = self.env['ir.sequence'].create(seq)
		seq_date_range = seq._get_current_sequence()
		seq_date_range.number_next = 1
		return seq
	

	def action_create_sequence(self):
		journal_ids = []
		for journal in self:
			journal_ids.append(journal.id)
		wizard = self.env['account.sequence.journal.wizard'].create({'name':'Generar Secuencias',
							       'journal_ids':[(6, 0, journal_ids)]})
		return {
			'res_id':wizard.id,
			'view_type':'form',
			'view_mode':'form',
			'res_model':'account.sequence.journal.wizard',
			'views':[[self.env.ref('account_journal_sequence.view_account_sequence_journal_wizard_form').id,'form']],
			'type':'ir.actions.act_window',
			'target':'new'
		}