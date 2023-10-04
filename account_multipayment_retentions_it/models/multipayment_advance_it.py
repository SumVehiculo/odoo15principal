# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class MultipaymentAdvanceIt(models.Model):
	_inherit = 'multipayment.advance.it'
	
	is_retention = fields.Boolean(string=u'Aplicar retención',default=False)
	retention_number = fields.Char(string=u'Nro Comprobante Retención')

	def calculate_line(self):
		if self.is_retention:
			param = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1)
			if not param.retention_account_id:
				raise UserError(u'No tiene establecida la cuenta para Retenciones en los parametros principales de su Compañía.')
			if not param.retention_percentage:
				raise UserError(u'No tiene establecido el porcentaje para Retenciones en los parametros principales de su Compañía.')
			if not self.retention_number:
				raise UserError(u'No tiene establecido el Nro de Comprobante de Retención en la pestaña Otra información')
			
			amount = 0
			for invoice in self.invoice_ids.filtered(lambda line: line.account_id.user_type_id.type in ('receivable', 'payable')):
				amount+= (invoice.debe - invoice.haber)
			doc = self.env['l10n_latam.document.type'].search([('code','=','00')],limit=1)
			val = {
				'main_id': self.id,
				'account_id': param.retention_account_id.id,
				'importe_divisa': 0,
				'debe': 0 if ((amount*param.retention_percentage)) > 0 else abs(amount*param.retention_percentage),
				'haber': (amount*param.retention_percentage) if (amount*param.retention_percentage) > 0 else 0,
				'partner_id': self.partner_cash_id.id,
				'type_document_id': doc.id,
				'nro_comp': self.retention_number
			}
			self.env['multipayment.advance.it.line2'].create(val)
				

		return super(MultipaymentAdvanceIt, self).calculate_line()