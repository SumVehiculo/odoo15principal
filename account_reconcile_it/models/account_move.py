# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class AccountMove(models.Model):
	_inherit = 'account.move'
	
	#Conciliacion al publicar asientos de Apertura/Cierre
	def _post(self, soft=True):
		to_post = super(AccountMove,self)._post(soft=soft)
		for move in to_post:
			if move.is_opening_close and move.move_type == 'entry':
				journal_ids = self.env['account.main.parameter'].search([('company_id','=',move.company_id.id)],limit=1).opening_close_journal_ids
				if journal_ids:
					if move.journal_id in journal_ids.ids:
						self._cr.execute("""update account_move set amount_residual = 0, amount_residual_signed = 0, payment_state ='paid' where id = %d"""%(move.id))
						self._cr.execute("""update account_move_line set amount_residual = 0, amount_residual_currency = 0, reconciled=TRUE where move_id = %d"""%(move.id))
						move._compute_payments_widget_to_reconcile_info()
		return to_post