# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError
from datetime import date

class AccountCodeSunatTable(models.Model):
	_name = 'account.code.sunat.table'

	name = fields.Char(string=u'Codigo')