# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class AccountBankStatementLine(models.Model):
	_inherit = 'account.bank.statement.line'

	catalog_payment_id = fields.Many2one('einvoice.catalog.payment',string='Medio de Pago')
	type_document_id = fields.Many2one('l10n_latam.document.type',string='T.D.',copy=False)
	account_cash_flow_id = fields.Many2one('account.cash.flow',string='Tipo Flujo de Caja')
	
class AccountBankStatement(models.Model):
	_inherit = 'account.bank.statement'

	journal_check_surrender = fields.Boolean(string='Para rendiciones', related='journal_id.check_surrender', store=True)
	##DATOS RENDICION
	date_surrender = fields.Date(string='Fecha Entrega')
	employee_id = fields.Many2one('res.partner',string='Empleado')
	amount_surrender = fields.Float(string='Monto Entregado',default=0)
	einvoice_catalog_payment_id = fields.Many2one('einvoice.catalog.payment',string='Medio de Pago', copy=False)
	memory = fields.Char(string=u'Memoria')
	date_render_it = fields.Date(string=u'Fecha Rendición')