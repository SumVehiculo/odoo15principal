# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountAccount(models.Model):
	_inherit = 'account.account'
	
	account_integrated_result_id = fields.Many2one('account.integrated.results.catalog',string='Resultados Integrales')