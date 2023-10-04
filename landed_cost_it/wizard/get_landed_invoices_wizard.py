# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class GetLandedInvoices(models.TransientModel):
	_name = "get.landed.invoices.wizard"
	
	landed_id = fields.Many2one('landed.cost.it',string='Gasto Vinculado')
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	invoices_ids = fields.Many2many('account.move.line',string=u'Invoices', required=True,
	domain="[('display_type','=',False),('parent_state','=','posted'),('is_landed','=',True),('company_id','=',company_id)]")
		
	def insert(self):
		vals=[]
		for invoice in self.invoices_ids:
			invoice_exist = self.env['landed.cost.invoice.line'].search([('invoice_id','=',invoice.id)],limit=1)
			if invoice_exist:
				raise UserError('Esta intentando ingresar una Factura que ya existe en otro Gasto Vinculado (%s)'%str(invoice_exist.landed_id.id))
			val = {
				'landed_id': self.landed_id.id,
				'invoice_id': invoice.id,
				'invoice_date': invoice.invoice_date_landed,
				'type_document_id': invoice.type_document_id.id,
				'nro_comp': invoice.nro_comp,
				'date': invoice.date,
				'partner_id': invoice.partner_id.id,
				'product_id': invoice.product_id.id,
				'debit': invoice.debit,
				'amount_currency': invoice.amount_currency if invoice.move_id.currency_id != invoice.company_id.currency_id else invoice.debit/(invoice.tc or 1),
				'tc': invoice.tc,
				'type_landed_cost_id': invoice.product_id.type_landed_cost_id.id,
				'company_id': invoice.company_id.id,
			}
			vals.append(val)
		self.env['landed.cost.invoice.line'].create(vals)
		self.landed_id._change_flete()