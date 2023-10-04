# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class AccountAccount(models.Model):
	_inherit = 'account.account'

	@api.constrains('internal_type','is_document_an')
	def constraint_reconcile(self):
		for i in self:
			if i.internal_type in ('payable','receivable') and not i.is_document_an:
				raise UserError(u'Es obligatorio que el campo Tiene Analisis por Documento este marcado si la cuenta es Por Cobrar y Por Pagar. Cuenta (%s)'%(i.code))