# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountBookLedgerView(models.Model):
	_inherit = 'account.book.ledger.view'
	
	eti_analitica = fields.Char(string=u'Eti. Analítica')