# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError

class AccountMove(models.Model):
	_inherit = 'account.move'

	landed_cost_id = fields.Many2one('landed.cost.it',string='Gasto Vinculado')