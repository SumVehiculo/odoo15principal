# -*- coding: utf-8 -*-

from odoo import models, fields, api

class SurrenderFreeIt(models.Model):
	_name = 'surrender.free.it'
	
	period_id = fields.Many2one('account.period',string=u'Periodo')
	move_id = fields.Many2one('account.move',string=u'Asiento')
	company_id = fields.Many2one('res.company',string='Compañia',required=True,default=lambda self: self.env.company,readonly=True)