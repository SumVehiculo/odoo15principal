# -*- encoding: utf-8 -*-
from odoo import fields, models, _

class AccountJournal(models.Model):
	_inherit = 'account.journal'

	despatch_sequence_id = fields.Many2one('ir.sequence', string='Secuencia de Guia')
