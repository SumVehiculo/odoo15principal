# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class AccountMove(models.Model):
	_inherit = 'account.move'

	def action_apply_quotes_nro_comp_it(self):
		for move in self:
			if move.move_type in ['out_invoice', 'in_invoice', 'out_refund', 'in_refund']:
				if move.state != 'posted':
					raise UserError(u"No puede aplicar esta accion si la Factura no esta publicada")
				count = 1
				for line in move.line_ids:
					
					if line.account_id.internal_type in ('receivable','payable'):
						line.nro_comp = line.nro_comp + ' - C' + str(count)
						count += 1

		return self.env['popup.it'].get_message('Se aplicaron correlativos a nros de Comprobantes.')