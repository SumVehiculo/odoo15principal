# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class AccountAssetMoveIt(models.Model):
	_name = 'account.asset.move.it'
	_description = 'Asset Move IT'

	period_id = fields.Many2one('account.period',string='Periodo',required=True)
	move_id = fields.Many2one('account.move',string='Asiento')
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)