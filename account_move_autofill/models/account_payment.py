# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class AccountPayment(models.Model):
	_inherit = 'account.payment'

	@api.onchange('cash_nro_comp','type_doc_cash_id')
	def _get_ref(self):
		digits_serie = ('').join(self.type_doc_cash_id.digits_serie*['0'])
		digits_number = ('').join(self.type_doc_cash_id.digits_number*['0'])
		if self.cash_nro_comp:
			if '-' in self.cash_nro_comp:
				partition = self.cash_nro_comp.split('-')
				if len(partition) == 2:
					serie = digits_serie[:-len(partition[0])] + partition[0]
					number = digits_number[:-len(partition[1])] + partition[1]
					self.cash_nro_comp = serie + '-' + number

	@api.onchange('nro_comp','type_document_id')
	def _get_ref(self):
		digits_serie = ('').join(self.type_document_id.digits_serie*['0'])
		digits_number = ('').join(self.type_document_id.digits_number*['0'])
		if self.nro_comp:
			if '-' in self.nro_comp:
				partition = self.nro_comp.split('-')
				if len(partition) == 2:
					serie = digits_serie[:-len(partition[0])] + partition[0]
					number = digits_number[:-len(partition[1])] + partition[1]
					self.nro_comp = serie + '-' + number