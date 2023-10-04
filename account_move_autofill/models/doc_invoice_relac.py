# -*- coding: utf-8 -*-

from odoo import models, fields, api

class DocInvoiceRelac(models.Model):
	_inherit = 'doc.invoice.relac'

	@api.onchange('nro_comprobante','type_document_id')
	def _get_ref(self):
		digits_serie = ('').join(self.type_document_id.digits_serie*['0'])
		digits_number = ('').join(self.type_document_id.digits_number*['0'])
		if self.nro_comprobante:
			if '-' in self.nro_comprobante:
				partition = self.nro_comprobante.split('-')
				if len(partition) == 2:
					serie = digits_serie[:-len(partition[0])] + partition[0]
					number = digits_number[:-len(partition[1])] + partition[1]
					self.nro_comprobante = serie + '-' + number
