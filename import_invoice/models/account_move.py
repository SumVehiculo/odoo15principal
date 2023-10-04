# -*- coding: utf-8 -*-

from odoo import models, fields, exceptions, api

class AccountMove(models.Model):
	_inherit = "account.move"

	import_invoice_it_id = fields.Many2one('import.invoice.it',string='Codigo de Importacion Invoice',ondelete="cascade",copy=False)
	custom_seq = fields.Boolean('Custom Sequence')
	system_seq = fields.Boolean('System Sequence')
	invoice_name = fields.Char('Invoice Name')