# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class AccountMoveLine(models.Model):
	_inherit = 'account.move.line'

	def reconcile(self):
		type_document = None
		nro_comp = None
		for line in self:
			if type_document is None:
				type_document = line.type_document_id
			elif line.type_document_id != type_document:
				raise UserError("Apuntes no tienen el mismo Tipo de documento: %s != %s"
								% ((type_document.code or '') + ' ' + (type_document.name or ''), (line.type_document_id.code or '') +' '+ (line.type_document_id.name or '')))
			if nro_comp is None:
				nro_comp = line.nro_comp
			elif line.nro_comp != nro_comp:
				raise UserError("Apuntes no tienen el mismo Numero de Comprobante: %s != %s"
								% ((nro_comp or ''), (line.nro_comp or '')))
		res = super().reconcile()

		return res