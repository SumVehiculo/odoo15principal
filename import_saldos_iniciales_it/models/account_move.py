# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class AccountMove(models.Model):
	_inherit = 'account.move'

	apertura_id = fields.Many2one('import.move.apertura.it',string='Apertura ID',copy=False)