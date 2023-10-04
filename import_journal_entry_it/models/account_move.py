# -*- coding: utf-8 -*-

from odoo import models, fields, exceptions, api

class AccountMove(models.Model):
	_inherit = "account.move"

	import_journal_entry_it_id = fields.Many2one('import.journal.entry.it',string='Codigo de Importacion',ondelete="cascade",copy=False)