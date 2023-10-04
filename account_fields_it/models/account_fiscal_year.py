# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountFiscalYear(models.Model):
	_inherit = "account.fiscal.year"

	period_ids = fields.One2many('account.period','fiscal_year_id',string='Periodos')

	def open_periods(self):
		self.ensure_one()
		action = self.env.ref('account_base_it.action_account_period_form').read()[0]
		domain = [('id', 'in', self.period_ids.ids)]
		context = dict(self.env.context, default_fiscal_year_id=self.id)
		views = [(self.env.ref('account_base_it.view_account_period_list').id, 'tree'), (False, 'form'), (False, 'kanban')]
		return dict(action, domain=domain, context=context, views=views)