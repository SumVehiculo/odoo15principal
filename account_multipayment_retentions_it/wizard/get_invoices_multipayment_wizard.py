# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _

class GetInvoicesMultipaymentWizard(models.TransientModel):
	_inherit = "get.invoices.multipayment.wizard"
	
	partner_cash_id = fields.Many2one('res.partner',string='Partner Caja')

	@api.model
	def _getDomainInvoices(self):
		#type_selection = ''
		#company_id = 1
		domain = "[('display_type','=',False),('parent_state','=','posted'),('partner_id','!=',False),('type_document_id','!=',False),('account_internal_type','in',['payable','receivable']),('amount_residual','!=',0),('reconciled','=',False),('account_internal_type', '=', type_selection),('company_id','=',company_id)%s]"%(",('partner_id','=',partner_cash_id)" if self.partner_cash_id else "")
		#if self.partner_cash_id:
		#	partner_cash_id = 1
		#	domain.append(('partner_id','=',partner_cash_id))
		return domain

	invoices = fields.Many2many('account.move.line',string=u'Line Invoices', required=True)
