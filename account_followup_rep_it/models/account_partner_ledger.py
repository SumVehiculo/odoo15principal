# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, api, _, _lt, fields
from odoo.tools.misc import format_date
from datetime import timedelta


class ReportPartnerLedger(models.AbstractModel):
	_inherit = "account.partner.ledger"

	@api.model
	def _get_report_line_move_line(self, options, partner, aml, cumulated_init_balance, cumulated_balance):
		aml_dict = super(ReportPartnerLedger,self)._get_report_line_move_line(options, partner,aml,cumulated_init_balance,cumulated_balance)
		aml_dict['name'] =  aml['ref']
		return aml_dict