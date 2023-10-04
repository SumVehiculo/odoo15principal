# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError

class DeleteReversedMove(models.TransientModel):
	_name = 'delete.reversed.move'
	_description = 'Delete Reversed Move'

	period_from = fields.Many2one('account.period',string='Periodo Inicial')
	period_to = fields.Many2one('account.period',string='Periodo Final')

	def delete_reversed_moves(self):
		
		self._cr.execute('''
			SELECT ID,REVERSED_ENTRY_ID FROM ACCOUNT_MOVE 
			WHERE (REVERSED_ENTRY_ID IS NOT NULL AND MOVE_TYPE = 'entry' AND COMPANY_ID = %d AND JOURNAL_ID = %d
			AND (DATE BETWEEN '%s' AND '%s')) ORDER BY ID
		''' % (self.env.company.id,self.env.company.currency_exchange_journal_id.id,self.period_from.date_start.strftime('%Y/%m/%d'),
				self.period_to.date_end.strftime('%Y/%m/%d')))

		for row in self._cr.fetchall():
			reversed_move = self.env['account.move'].browse(row[1])
			move = self.env['account.move'].browse(row[0])

			for mm in move.line_ids:
				mm.remove_move_reconcile()
			move.button_cancel()
			move.line_ids.unlink()
			move.name = "/"
			move.unlink()

			reversed_move.button_cancel()
			reversed_move.line_ids.unlink()
			reversed_move.name = "/"
			reversed_move.unlink()

		return self.env['popup.it'].get_message('SE ELIMINARON LOS ASIENTOS DE REVERSION DE MANERA CORRECTA.')