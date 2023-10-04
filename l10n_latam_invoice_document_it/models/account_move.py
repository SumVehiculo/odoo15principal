# -*- coding: utf-8 -*-

from odoo import models, fields, exceptions, api

class AccountMove(models.Model):
	_inherit = "account.move"

	def _compute_l10n_latam_document_type(self):
		for rec in self.filtered(lambda x: x.state == 'draft'):
			rec.l10n_latam_document_type_id = rec.l10n_latam_document_type_id.id
	
	@api.depends('ref')
	def _compute_l10n_latam_document_number(self):
		recs_with_name = self.filtered(lambda x: x.ref != '')
		for rec in recs_with_name:
			name = rec.ref
			doc_code_prefix = rec.l10n_latam_document_type_id.doc_code_prefix
			if doc_code_prefix and name:
				name = name.split(" ", 1)[-1]
			rec.l10n_latam_document_number = name
		remaining = self - recs_with_name
		remaining.l10n_latam_document_number = False

	@api.onchange('l10n_latam_document_type_id', 'l10n_latam_document_number')
	def _inverse_l10n_latam_document_number(self):
		for rec in self.filtered(lambda x: x.l10n_latam_document_type_id):
			if not rec.l10n_latam_document_number:
				rec.ref = ''
			else:
				l10n_latam_document_number = rec.l10n_latam_document_type_id._format_document_number(rec.l10n_latam_document_number)
				if rec.l10n_latam_document_number != l10n_latam_document_number:
					rec.l10n_latam_document_number = l10n_latam_document_number
				rec.ref = "%s%s" % (rec.l10n_latam_document_type_id.doc_code_prefix, l10n_latam_document_number)