# -*- coding: utf-8 -*-

from odoo import models, fields, api

class SurrenderFreeConcepts(models.Model):
	_name = 'surrender.free.concepts'

	name = fields.Char(string='Concepto')
	account_analytic_tag_id = fields.Many2one('account.analytic.tag',string=u'Etiqueta Analítica')
	expense_account_id = fields.Many2one('account.account',string=u'Cuenta de Gasto')
	
	company_id = fields.Many2one('res.company',string='Compañia',required=True,default=lambda self: self.env.company,readonly=True)