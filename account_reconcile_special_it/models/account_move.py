from odoo import models, api, _
from odoo.exceptions import UserError


class AccountMove(models.Model):
	_inherit = "account.move"

	def action_concile_special(self):
		for move in self:
			apply = False
			if move.move_type in ('out_invoice','out_refund','in_invoice','in_refund'):
				if move.amount_residual == move.amount_total:
					apply = True
				else:
					raise UserError('No se puede aplicar la conciliacion especial ya que tiene pagos parciales.')
			else:
				apply = True
			
			if apply:
				self.env.cr.execute("""update account_move set amount_residual = 0, amount_residual_signed = 0, payment_state='paid' where id = %d"""%(move.id))
				self.env.cr.execute("""update account_move_line set amount_residual = 0, amount_residual_currency = 0, reconciled=TRUE where move_id = %d"""%(move.id))
				self._compute_payments_widget_to_reconcile_info()
		return self.env['popup.it'].get_message(u'Se aplicó la conciliación especial.')

	def action_reconcile_special(self):
		for move in self:
			self.env.cr.execute("""update account_move set amount_residual = amount_total, amount_residual_signed = amount_total_signed, payment_state='not_paid' where id = %d"""%(move.id))
			self.env.cr.execute("""update account_move_line set reconciled=FALSE, amount_residual = (debit - credit) , amount_residual_currency = amount_currency where move_id = %d"""%(move.id))
				
		return self.env['popup.it'].get_message(u'Se quitó la conciliación especial.')