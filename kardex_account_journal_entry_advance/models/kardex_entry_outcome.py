# -*- coding: utf-8 -*-

from odoo import models, fields, api

class KardexEntryOutcomeIt(models.Model):
	_name = 'kardex.entry.outcome.it'
	
	period_id = fields.Many2one('account.period',string=u'Periodo')
	move_ids = fields.One2many('account.move','kardex_outcome_id',string=u'Asientos')
	company_id = fields.Many2one('res.company',string='Compañia',required=True,default=lambda self: self.env.company,readonly=True)