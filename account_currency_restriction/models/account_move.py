# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.addons.payment.models.payment_acquirer import ValidationError

class AccountMove(models.Model):
	_inherit = 'account.move'
	
	def _post(selfs, soft=True):
		for self in selfs:
			for line in self.line_ids:
				if self.currency_id.name != 'PEN' and line.account_id.user_type_id.type in ['receivable','payable'] and line.account_id.currency_id != self.currency_id and self.move_type != 'entry':
					raise ValidationError('No se puede crear una Factura con moneda extranjera sin cuentas con moneda extranjera')
				if self.currency_id.id == self.env.company.currency_id.id and line.account_id.user_type_id.type in ['receivable','payable'] and line.account_id.currency_id and self.move_type != 'entry':
					raise ValidationError('No se puede crear una Factura con moneda PEN y cuentas con moneda definida')
		to_post = super(AccountMove,selfs)._post(soft=soft)
		return to_post