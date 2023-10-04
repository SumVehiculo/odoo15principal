# -*- coding: utf-8 -*-

from odoo import models, fields, exceptions, api

class AccountMove(models.Model):
	_inherit = "account.move"

	opening_id_it = fields.Many2one('account.opening.it',string='ID Apertura',copy=False)