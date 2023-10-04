# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ItInvoiceSerie(models.Model):
	_name = 'it.invoice.serie'

	name = fields.Char(string='Nombre')
	type_document_id = fields.Many2one('l10n_latam.document.type',string='Tipo de Documento')
	sequence_id = fields.Many2one('ir.sequence',string='Secuencia')
	manual = fields.Boolean(string='Es manual', default=False)
	company_id = fields.Many2one('res.company',string=u'Compañía',default=lambda self: self.env.company,required=True,readonly=True)