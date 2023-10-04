# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class AccountMove(models.Model):
	_inherit = 'account.move'

	sequence_number_it = fields.Char(string='Backup Number')

	@api.onchange('serie_id')
	def onchange_serie_id(self):
		if not self.name or self.name == '/':
			if self.serie_id:
				next_number = self.serie_id.sequence_id.number_next_actual
				if not self.serie_id.sequence_id.prefix:
					raise UserError("No existe un prefijo configurado en la secuencia de la serie.")
				prefix = self.serie_id.sequence_id.prefix
				padding = self.serie_id.sequence_id.padding
				self.ref = prefix + "0"*(padding - len(str(next_number))) + str(next_number)

	def action_post(selfs):
		self = selfs
		res = super(AccountMove,self).action_post()
		if self.move_type != 'entry':
			name = self.name
			if (self.sequence_number_it != self.ref):
				if self.serie_id.sequence_id:
					if not self.serie_id.sequence_id.prefix:
						raise UserError("No existe un prefijo configurado en la secuencia de la serie.")
					sequence = self.serie_id.sequence_id
					next_number =sequence.number_next_actual
					serie = str(next_number).rjust(sequence.padding, '0')
					serie = (sequence.prefix or '') + serie + (sequence.suffix or '')
					name = serie

					sequence.number_next_actual = next_number + self.serie_id.sequence_id.number_increment
					self.ref = name
					self.sequence_number_it = name

		return res


