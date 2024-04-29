# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools

class AccountBookHonoraryView(models.Model):
	_inherit = 'account.book.honorary.view'


	name = fields.Char(string='Nombre')
	