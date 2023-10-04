# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class ValidationSqlWizard(models.TransientModel):
	_name = 'validation.sql.wizard'
	_description = 'validation Sql Wizard'

	querydeluxe_id = fields.Many2one('querydeluxe')
	pin = fields.Char(string=u'Código PIN')

	def validate(self):
		if self.pin == '$K4&K3&6U$R1%5QL':
			self.querydeluxe_id.execute()
		else:
			raise UserError(u'PIN INCORRECTO.')