# -*- coding: utf-8 -*-

from odoo import models, fields, api

class MultipaymentAdvanceIt(models.Model):
	_inherit = 'multipayment.advance.it'

	detraction_lot_number = fields.Char(string=u'Número de Lote de Detracciones',size=6)
	is_detraction_payment = fields.Boolean(string='Es Pago de Detracciones',default=False)

	def get_pay_detractions_wizard(self):
		wizard = self.env['massive.payment.detractions.wizard'].create({
			'multipayment_id': self.id
		})
		module = __name__.split('addons.')[1].split('.')[0]
		view = self.env.ref('%s.view_massive_payment_detractions_wizard_form' % module)
		return {
			'name':u'Pago Masivo de Detracciones',
			'res_id':wizard.id,
			'view_mode': 'form',
			'res_model': 'massive.payment.detractions.wizard',
			'view_id': view.id,
			'context': self.env.context,
			'target': 'new',
			'type': 'ir.actions.act_window',
		}

class MultipaymentAdvanceItLine(models.Model):
	_inherit = 'multipayment.advance.it.line'

	tc = fields.Float(string='Tipo Cambio',digits=(12,3),default=1)

	@api.onchange('importe_divisa','tc')
	def _update_debit_credit(self):
		if self.importe_divisa:
			if self.tc == 1:
				self.tc = self.main_id.tc
			tc = self.tc if self.main_id.is_detraction_payment else self.main_id.tc
			if self.invoice_id.currency_id and self.invoice_id.currency_id != self.invoice_id.company_id.currency_id:
				self.debe = self.importe_divisa * tc if self.importe_divisa > 0 else 0
				self.haber = 0 if self.importe_divisa > 0 else abs(self.importe_divisa * tc)
			else:
				self.debe = self.importe_divisa if self.importe_divisa > 0 else 0
				self.haber = 0 if self.importe_divisa > 0 else abs(self.importe_divisa)