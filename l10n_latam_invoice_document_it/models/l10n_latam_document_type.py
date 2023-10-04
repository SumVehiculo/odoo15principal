# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class L10nLatamDocumentType(models.Model):
	_inherit = 'l10n_latam.document.type'

	@api.model
	def _del_document_type_odoo(self):
		ids = []
		ids.append(self.env.ref('l10n_pe.document_type01').id)
		ids.append(self.env.ref('l10n_pe.document_type02').id)
		ids.append(self.env.ref('l10n_pe.document_type07').id)
		ids.append(self.env.ref('l10n_pe.document_type07b').id)
		ids.append(self.env.ref('l10n_pe.document_type08').id)
		ids.append(self.env.ref('l10n_pe.document_type20').id)
		ids.append(self.env.ref('l10n_pe.document_type40').id)
		self.search([('id','not in',ids)]).unlink()
	
	def _get_ref(self,nro_comp):
		digits_serie = ('').join(self.digits_serie*['0'])
		digits_number = ('').join(self.digits_number*['0'])
		if nro_comp:
			if '-' in nro_comp:
				partition = nro_comp.split('-')
				if len(partition) == 2:
					serie = digits_serie[:-len(partition[0])] + partition[0]
					number = digits_number[:-len(partition[1])] + partition[1]
					new_nro_comp = serie + '-' + number
					return new_nro_comp

		return nro_comp