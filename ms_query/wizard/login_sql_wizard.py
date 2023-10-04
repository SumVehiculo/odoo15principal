# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class LoginSqlWizard(models.TransientModel):
	_name = 'login.sql.wizard'
	_description = 'Login Sql Wizard'

	ms_query_id = fields.Many2one('ms.query')
	pin = fields.Char(string=u'Código PIN')

	def validate(self):
		if self.pin == '$K4&K3&6U$R1%5QL':
			self.ms_query_id.execute_query()
		else:
			raise UserError(u'PIN INCORRECTO.')