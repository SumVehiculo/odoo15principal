# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class AccountTemplateMultipayment(models.Model):
	_name = 'account.template.multipayment'

	name = fields.Char(string='Concepto',required=True)
	account_id = fields.Many2one('account.account',string='Cuenta',required=True)
	analytic_account_id = fields.Many2one('account.analytic.account', string='Cta Analitica')
	analytic_tag_id = fields.Many2one('account.analytic.tag', string='Etiqueta Analitica')
	company_id = fields.Many2one('res.company',string=u'Compañía',default=lambda self: self.env.company)