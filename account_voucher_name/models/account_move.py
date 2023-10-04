# -*- coding: utf-8 -*-
from odoo import models, fields, api, _ 
from odoo.exceptions import UserError, ValidationError

class AccountMove(models.Model):
	_inherit = 'account.move'

	name = fields.Char(compute="_compute_name_by_sequence",inverse='_set_name_it')
	# highest_name, sequence_prefix and sequence_number are not needed any more
	# -> compute=False to improve perf
	highest_name = fields.Char(compute=False)
	sequence_prefix = fields.Char(compute=False)
	sequence_number = fields.Integer(compute=False)

	_sql_constraints = [
		(
			"name_state_diagonal",
			"CHECK(COALESCE(name, '') NOT IN ('/', '') OR state!='posted')",
			'A move can not be posted with name "/" or empty value\n'
			"Check the journal sequence, please",
		),
	]

	@api.depends("state", "journal_id", "date")
	def _compute_name_by_sequence(self):
		for move in self:
			name = move.name or "/"
			# I can't use posted_before in this IF because
			# posted_before is set to True in _post() at the same
			# time as state is set to "posted"
			if (move.state == "posted" and (not move.name or move.name == "/") and move.journal_id and move.journal_id.sequence_id_it):
				seq = move.journal_id.sequence_id_it
				name = seq.next_by_id(sequence_date=move.date)
			move.name = name
	
	def _set_name_it(self):
		pass

	# We must by-pass this constraint of sequence.mixin
	def _constrains_date_sequence(self):
		return True

	def _is_end_of_seq_chain(self):
		invoices_no_gap_sequences = self.filtered(
			lambda inv: inv.journal_id.sequence_id_it.implementation == "no_gap"
		)
		invoices_other_sequences = self - invoices_no_gap_sequences
		if not invoices_other_sequences and invoices_no_gap_sequences:
			return False
		return super(AccountMove, invoices_other_sequences)._is_end_of_seq_chain()


	#FUNCION PARA CAMBIAR DISPLAY NAME A NUM_VOU (ES PARTE DEL CAMPO)
	#def _get_move_display_name(self, show_ref=False):
	#	self.ensure_one()
	#	name = ''
	#	if self.state == 'draft':
	#		name += {
	#			'out_invoice': _('Draft Invoice'),
	#			'out_refund': _('Draft Credit Note'),
	#			'in_invoice': _('Draft Bill'),
	#			'in_refund': _('Draft Vendor Credit Note'),
	#			'out_receipt': _('Draft Sales Receipt'),
	#			'in_receipt': _('Draft Purchase Receipt'),
	#			'entry': _('Draft Entry'),
	#		}[self.move_type]
	#		name += ' '
	#	if not self.num_vou or self.num_vou == '/':
	#		name += '(* %s)' % str(self.id)
	#	else:
	#		name += self.num_vou
	#	return name + (show_ref and self.ref and ' (%s%s)' % (self.ref[:50], '...' if len(self.ref) > 50 else '') or '')
	
	#def _post(self, soft=True):
	#	to_post = super(AccountMove,self)._post(soft=soft)
	#	for move in to_post:
	#		if move.num_vou == '/':
	#			sequence = move.journal_id.sequence_id_it
	#			if sequence:
	#				to_write = sequence.with_context(ir_sequence_date=move.date).next_by_id()
	#				move.write({'num_vou': to_write})
	#	return to_post
	
	def action_change_name_it(self):
		for move in self:
			if move.state == 'draft':
				move.name = '/'
				move.posted_before = False
			else:
				raise UserError("No puede alterar el nombre si no se encuentra en estado Borrador")

		return self.env['popup.it'].get_message('Se borro correctamente la secuencia.')
	
	@api.constrains('name', 'journal_id', 'state','date')
	def _check_unique_sequence_number(self):
		moves = self.filtered(lambda move: move.state == 'posted')
		if not moves:
			return

		self.flush(['name', 'journal_id', 'move_type', 'state'])

		# /!\ Computed stored fields are not yet inside the database.
		self._cr.execute('''
			SELECT move2.id
			FROM account_move move
			INNER JOIN account_move move2 ON
				move2.name = move.name
				AND move2.journal_id = move.journal_id
				AND move2.move_type = move.move_type
				AND EXTRACT (YEAR FROM move2.date) = EXTRACT (YEAR FROM move.date) 
				AND move2.id != move.id
			WHERE move.id IN %s AND move2.state = 'posted'
		''', [tuple(moves.ids)])
		res = self._cr.fetchone()
		if res:
			raise ValidationError(u'El asiento de diario publicado debe tener un número de secuencia único por empresa.')