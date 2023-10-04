# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountMainParameter(models.Model):
	_inherit = 'account.main.parameter'
	
	retention_journal_id = fields.Many2one('account.journal', string='Diario de Retenciones')