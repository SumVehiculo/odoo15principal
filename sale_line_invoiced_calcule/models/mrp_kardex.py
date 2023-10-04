# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError
from datetime import *
from datetime import timedelta

class sale_order_line(models.Model):
	_inherit = 'sale.order.line'

	@api.depends('invoice_lines.move_id.state', 'invoice_lines.quantity', 'untaxed_amount_to_invoice')
	def _compute_qty_invoiced(self):
		"""
		Compute the quantity invoiced. If case of a refund, the quantity invoiced is decreased. Note
		that this is the case only if the refund is generated from the SO and that is intentional: if
		a refund made would automatically decrease the invoiced quantity, then there is a risk of reinvoicing
		it automatically, which may not be wanted at all. That's why the refund has to be created from the SO
		"""
		for line in self:
			qty_invoiced = 0.0
			for invoice_line in line._get_invoice_lines():
				if invoice_line.move_id.state != 'cancel':
					if invoice_line.move_id.move_type == 'out_invoice':
						qty_invoiced += invoice_line.product_uom_id._compute_quantity(invoice_line.quantity, line.product_uom)
					elif invoice_line.move_id.move_type == 'out_refund' and invoice_line.move_id.l10n_pe_dte_credit_note_type not in ('04','05','09'):
						qty_invoiced -= invoice_line.product_uom_id._compute_quantity(invoice_line.quantity, line.product_uom)
			line.qty_invoiced = qty_invoiced