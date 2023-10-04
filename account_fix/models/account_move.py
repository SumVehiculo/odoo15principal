# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
import re

class AccountMove(models.Model):
	_inherit = 'account.move'
	
	@api.depends('company_id', 'invoice_filter_type_domain')
	def _compute_suitable_journal_ids(self):
		for m in self:
			journal_type = m.invoice_filter_type_domain
			company_id = m.company_id.id or self.env.company.id
			if journal_type:
				domain = [('company_id', '=', company_id), ('type', '=', journal_type)]
			else:
				domain = [('company_id', '=', company_id)]
			m.suitable_journal_ids = self.env['account.journal'].search(domain)
	
	def _post(self, soft=True):
		for move in self:
			if move.move_type != 'entry':
				filtered_line = move.line_ids.filtered(lambda l: not l.display_type and l.debit==0 and l.credit==0 and l.amount_currency == 0 and not l.tax_tag_ids)
				filtered_line.unlink()
		to_post = super(AccountMove,self)._post(soft=soft)
		return to_post
	
	@api.model_create_multi
	def create(self, vals_list):
		rslt = super(AccountMove, self).create(vals_list)
		rslt.name = "/"
		return rslt
	
	#@api.constrains('glosa')
	#def constraint_characters_glosa(self):
	#	pattern = r'^[a-zA-Z0-9]+$'
	#	for move in self:
	#		if move.glosa:
	#			if not re.match(pattern,move.glosa):
	#				raise UserError(u'El campo "Glosa" solo debe tener letras, números o un guión(-) : "%s"'%(move.glosa))
	
	#@api.constrains('ref')
	#def constraint_characters_ref(self):
	#	pattern = r'^[a-zA-Z0-9-]+$'
	#	for move in self:
	#		if move.ref:
	#			if not re.match(pattern,move.ref):
	#				raise UserError(u'El campo "Referencia/Número de Comprobante" solo debe tener letras, números o un guión(-) : "%s"'%(move.ref))

class AccountMoveLine(models.Model):
	_inherit = 'account.move.line'

	#@api.constrains('nro_comp')
	#def constraint_characters_nrocomp(self):
	#	pattern = r'^[a-zA-Z0-9-]+$'
	#	for line in self:
	#		if line.nro_comp:
	#			if not re.match(pattern,line.nro_comp):
	#				raise UserError(u'El campo "Número de Comprobante" solo debe tener letras, números o un guión(-) : "%s"'%(line.nro_comp))