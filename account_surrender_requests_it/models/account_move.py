# -*- coding: utf-8 -*-

from odoo import models, fields, exceptions, api

class AccountMove(models.Model):
	_inherit = "account.move"

	surrender_request_id = fields.Many2one('account.surrender.requests.it',string='Enlace Rendiciones',ondelete="cascade",copy=False)