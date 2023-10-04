# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountMainParameter(models.Model):
	_inherit = 'account.main.parameter'
	
	journal_exchange_exclude = fields.Many2many('account.journal', 'account_journal_main_parameter_rel', string='Diarios Excluidos para Conversion')