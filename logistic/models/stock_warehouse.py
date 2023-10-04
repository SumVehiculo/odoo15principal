# -*- encoding: utf-8 -*-
from odoo import fields, models, _

class StockWarehouse(models.Model):
	_inherit = 'stock.warehouse'

	despatch_journal_ids = fields.Many2many('account.journal', string='Journals (Sequences)', copy=False)
