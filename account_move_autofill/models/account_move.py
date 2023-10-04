# -*- coding: utf-8 -*-
from odoo import models, fields, api

class AccountMove(models.Model):
	_inherit = 'account.move'

	@api.onchange('ref','l10n_latam_document_type_id')
	def _get_ref(self):
		if self.move_type in ['out_invoice', 'in_invoice', 'out_refund', 'in_refund']:
			digits_serie = ('').join(self.l10n_latam_document_type_id.digits_serie*['0'])
			digits_number = ('').join(self.l10n_latam_document_type_id.digits_number*['0'])
			if self.ref:
				if '-' in self.ref:
					partition = self.ref.split('-')
					if len(partition) == 2:
						serie = digits_serie[:-len(partition[0])] + partition[0]
						number = digits_number[:-len(partition[1])] + partition[1]
						self.ref = serie + '-' + number

class AccountMoveLine(models.Model):
	_inherit = 'account.move.line'

	@api.onchange('nro_comp','type_document_id')
	def _get_ref(self):
		for i in self:
			digits_serie = ('').join(i.type_document_id.digits_serie*['0'])
			digits_number = ('').join(i.type_document_id.digits_number*['0'])
			if i.nro_comp:
				if '-' in i.nro_comp:
					partition = i.nro_comp.split('-')
					if len(partition) == 2:
						serie = digits_serie[:-len(partition[0])] + partition[0]
						number = digits_number[:-len(partition[1])] + partition[1]
						i.nro_comp = serie + '-' + number