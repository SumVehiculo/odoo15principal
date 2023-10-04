# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountDeferredExpenseView(models.Model):
	_name = 'account.deferred.expense.view'
	_auto = False
	
	invoice_date = fields.Date(string='Fecha Factura')
	partner = fields.Char(string='Partner')
	acquisition_date = fields.Char(string='Fecha Gasto')
	diario = fields.Char(string='Diario')
	asiento = fields.Char(string='Asiento')
	estado = fields.Char(string='Estado')
	glosa = fields.Char(string='Glosa')
	ref = fields.Char(string='Referencia')
	date = fields.Date(string='Fecha Contable')
	amount_total = fields.Float(string='Monto Gasto', digits=(64,2))