# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class AccountMove(models.Model):
	_inherit = 'account.move'

	personalize_tax = fields.Boolean(string="Impuesto Personalizado",default=False)
	
	def _post(self, soft=True):
		for elem in self:
			if elem.move_type in ['out_invoice', 'in_invoice', 'out_refund', 'in_refund']:
				for line in elem.line_ids:
					if not elem.personalize_tax:
						if len(line.tax_tag_ids.ids) > 0:
							line.tax_amount_it = -line.credit if line.credit > 0 else line.debit
							line.tax_amount_me = line.amount_currency if elem.currency_id != elem.company_id.currency_id else round(line.tax_amount_it/(elem.currency_rate or 1),2)
		return super(AccountMove,self)._post(soft=soft)