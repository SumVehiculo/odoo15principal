# -*- coding: utf-8 -*-
from odoo import models, fields, api

class CrossoveredBudgetLines(models.Model):
	_inherit = 'crossovered.budget.lines'

	amount_diff = fields.Monetary(compute='_compute_amount_diff', string='Diferencia', store=True)


	@api.depends('planned_amount','practical_amount')
	def _compute_amount_diff(self):
		for line in self:
			line.amount_diff = (line.planned_amount or 0) + (line.practical_amount or 0)