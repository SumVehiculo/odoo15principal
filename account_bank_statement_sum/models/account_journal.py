# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class account_journal(models.Model):
	_inherit = 'account.journal'
	
	amount_max = fields.Float('Monto Maximo de Gasto')