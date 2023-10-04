# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class AccountMove(models.Model):
	_inherit = 'account.move'

	def _post(self, soft=True):
		posted = super()._post(soft)
		for move in posted:
			for line in move.line_ids:
				line.check_nro_comp()
		return posted
	
	@api.constrains('line_ids','line_ids.account_id','line_ids.type_document_id','line_ids.nro_comp','line_ids.partner_id','state')
	def constrains_line_analisis(self):
		for move in self:
			for line in move.line_ids:
				line.check_nro_comp()

class AccountMoveLine(models.Model):
	_inherit = 'account.move.line'

	@api.constrains('account_id','type_document_id','nro_comp','partner_id')
	def constrains_nro_comp(self):
		for line in self:
			line.check_nro_comp()

	def check_nro_comp(self):
		for line in self:
			if line.account_id.is_document_an and (not line.type_document_id or not line.nro_comp or not line.partner_id):
				raise UserError('Para el apunte contable con cuenta %s es obligatorio el campo Tipo de Documento, Número de Comprobante y Socio.'%(line.account_id.code))