# -*- coding: utf-8 -*-
from odoo import models, fields, api

class account_analytic_tag(models.Model):
	_inherit = 'account.analytic.tag'

	description  = fields.Char(u'Descripción')
	