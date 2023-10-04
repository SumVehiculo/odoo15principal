# -*- coding: utf-8 -*-

from odoo import models, fields, exceptions, api

class AccountMove(models.Model):
	_inherit = "account.move"

	import_recxhon_id = fields.Many2one('import.recxhon.wizard',string='Codigo de Importacion Rec x Hon',ondelete="cascade",copy=False)