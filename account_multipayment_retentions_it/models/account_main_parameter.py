# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountMainParameter(models.Model):
	_inherit = 'account.main.parameter'
	
	retention_account_id = fields.Many2one('account.account',string='Cuenta de Retenciones')
	is_company_retention = fields.Boolean(string=u'Es agente de retención',default=False)
	retention_percentage = fields.Float(string=u'Porcentaje de Retención')