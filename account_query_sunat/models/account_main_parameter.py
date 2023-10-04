# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountMainParameter(models.Model):
	_inherit = 'account.main.parameter'

	client_id = fields.Char(string=u'Client ID')
	client_secret = fields.Char(string=u'Clave')
	token_expire = fields.Char(string='Token que expira')
	token_generation_date = fields.Datetime(string=u'Fecha de Generación de Token')
	token_expiration_date = fields.Datetime(string=u'Fecha de Vencimiento de Token')