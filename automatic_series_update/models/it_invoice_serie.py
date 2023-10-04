# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class ItInvoiceSerie(models.Model):
	_inherit = 'it.invoice.serie'

	prefix = fields.Char(string='Prefijo')
	type_document_id = fields.Many2one('l10n_latam.document.type',string='Tipo de Documento')
	sequence_id = fields.Many2one('ir.sequence',string='Secuencia')
	manual = fields.Boolean(string='Es manual', default=False)
	company_id = fields.Many2one('res.company',string=u'Compañía',default=lambda self: self.env.company,required=True,readonly=True)

	def create_sequence(self):
		if self.sequence_id:
			raise UserError(u'No puede volver a generar una secuencía si ya la tiene establecida, bórrela en su lugar.')
		if not self.prefix:
			raise UserError(u'Para crear la secuencia es obligatorio el Prefijo')
		seq = {
			'name': self.name,
			'implementation': 'standard',
			'prefix': self.prefix,
			'padding': 8,
			'number_increment': 1,
			'company_id': self.company_id.id
		}
		seq = self.env['ir.sequence'].create(seq)

		self.sequence_id = seq.id

		return self.env['popup.it'].get_message("Se ha generado correctamente la secuencia para '"+self.name+"'")