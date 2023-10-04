# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountMainParameter(models.Model):
	_inherit = 'account.main.parameter'

	sire_username = fields.Char(string=u'Usuario del generador')
	sire_password = fields.Char(string=u'Clave sol del generador')
	sire_client_id = fields.Char(string=u'SIRE Client ID')
	sire_client_secret = fields.Char(string=u'SIRE Clave')
	sire_token_expire = fields.Char(string='SIRE Token que expira')
	sire_token_generation_date = fields.Datetime(string=u'SIRE Fecha de Generación de Token')
	sire_token_expiration_date = fields.Datetime(string=u'SIRE Fecha de Vencimiento de Token')