# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class AccountMove(models.Model):
	_inherit = 'account.move'

	def action_anulate_invoice_it(self):
		MainParameter = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1)
		if not MainParameter.cancelation_partner:
			raise UserError(u'Falta configurar "Partner para Anulaciones" en Parametros Principales de su Compañía.')
		if not MainParameter.cancelation_product:
			raise UserError(u'Falta configurar "Producto para Anulaciones" en Parametros Principales de su Compañía.')
		for move in self:
			if move.state != 'cancel':
				raise UserError(u'No puede aplicar esta accion si la Factura/Asiento no esta Cancelada.')
			move.button_draft()
			if move.move_type != 'entry':
				l10n_latam_document_type_id = move.l10n_latam_document_type_id
				move.partner_id = MainParameter.cancelation_partner.id
				msale_state = self.env['ir.module.module'].search([('name', '=', 'sale')]).state
				if msale_state == 'msale_state':
					move.partner_shipping_id = MainParameter.cancelation_partner.id
				move.glosa = 'DOCUMENTO ANULADO'
				move.line_ids.with_context(check_move_validity=False).unlink()
				move._onchange_invoice_line_ids()

				fiscal_position = move.fiscal_position_id
				accounts = MainParameter.cancelation_product.product_tmpl_id.get_product_accounts(fiscal_pos=fiscal_position)
				if move.is_sale_document(include_receipts=True):
					move.campo_34_sale = '2'
					if not accounts['income']:
						raise UserError(u'Se necesita cuenta de Ingreso para "Producto para Anulaciones".')
					acc = accounts['income']
				elif move.is_purchase_document(include_receipts=True):
					move.campo_41_purchase = '0'
					if not accounts['expense']:
						raise UserError(u'Se necesita cuenta de Gastos para "Producto para Anulaciones".')
					acc = accounts['expense']

				vals = {
					'product_id' : MainParameter.cancelation_product.id,
					'quantity' : 1,
					'price_unit' :0,
					'name' : 'DOCUMENTO ANULADO',
					'account_id' : acc.id,
					'product_uom_id' : MainParameter.cancelation_product.uom_id.id,
					'company_id' : self.company_id.id
				}

				move.write({'invoice_line_ids' :([(0,0,vals)]) })
				for line in move.invoice_line_ids:
					line.tax_ids = line._get_computed_taxes()
				move._recompute_tax_lines()
				move.l10n_latam_document_type_id = l10n_latam_document_type_id
			else:
				move.glosa = 'DOCUMENTO ANULADO'
				move.line_ids.unlink()
				if not MainParameter.cancelation_product.property_account_income_id:
					raise UserError(u'Falta configurar "Cuenta de Ingreso" en "Producto para Anulaciones" de Parametros Principales de su Compañía.')
				vals = {
						'account_id': MainParameter.cancelation_product.property_account_income_id.id,
						'partner_id': MainParameter.cancelation_partner.id,
						'name': 'DOCUMENTO ANULADO',
						'debit': 0,
						'credit': 0,
						'company_id': self.company_id.id,
					}
				move.with_context(check_move_validity=False).write({'line_ids' :([(0,0,vals)]) })
			move.action_post()

		return self.env['popup.it'].get_message('Se aplicaron los cambios correctamente.')