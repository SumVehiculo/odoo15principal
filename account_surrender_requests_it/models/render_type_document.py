# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class RenderTypeDocument(models.Model):
	_name = 'render.type.document'

	code = fields.Char(string='Código', required=True)
	name = fields.Char(string=u'Descripción', required=True)
	type_document_id = fields.Many2one('l10n_latam.document.type',string='Documento SUNAT', required=True)

	def name_get(self):
		result = []
		for line in self:
			name = '(%s) %s'%(line.code,line.name)
			result.append((line.id, name))
		return result