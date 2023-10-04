# -*- encoding: utf-8 -*-

from odoo import api, fields, models, _

class GetInvoicesMultipaymentWizard(models.TransientModel):
	_name = "get.invoices.multipayment.wizard"
	
	type_selection = fields.Selection([('receivable','Ingresos'),('payable','Egresos')],string='Seleccionar',default='receivable')
	multipayment_id = fields.Many2one('multipayment.advance.it',string='P. Multiple')
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	invoices = fields.Many2many('account.move.line',string=u'Line Invoices', required=True, 
	domain="[('display_type','=',False),('parent_state','=','posted'),('partner_id','!=',False),('type_document_id','!=',False),('account_internal_type','in',['payable','receivable']),('reconciled','=',False),('account_internal_type', '=', type_selection),('company_id','=',company_id),'|',('amount_residual', '!=', 0.0),('amount_residual_currency', '!=', 0.0)]")
		
	def insert(self):
		vals=[]
		for invoice in self.invoices:
			residual_amount = 0
			if invoice.currency_id:
				residual_amount = invoice.amount_residual_currency
			else:
				residual_amount = invoice.amount_residual
			val = {
				'main_id': self.multipayment_id.id,
				'partner_id': invoice.partner_id.id,
				'tipo_documento': invoice.type_document_id.id,
				'invoice_id': invoice.id,
				'saldo': residual_amount,
				'operation_type': invoice.move_id.type_op_det,
				'good_services': invoice.move_id.detraction_percent_id.code,
				'cta_abono': invoice.move_id.acc_number_partner_id.id,
			}
			vals.append(val)
		self.env['multipayment.advance.it.line'].create(vals)