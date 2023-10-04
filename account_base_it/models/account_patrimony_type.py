# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountPatrimonyType(models.Model):
	_name = 'account.patrimony.type'

	name = fields.Char(string='Nombre')
	code = fields.Char(string='Codigo')