# -*- coding: utf-8 -*-

from odoo import models, fields, api

class CostsSalesAnalysisBook(models.Model):
	_name = 'costs.sales.analysis.book'
	_auto = False
	
	almacen = fields.Char(string=u'Almacén')
	producto = fields.Char(string=u'Producto')
	cantidad = fields.Float(string='Cantidad', digits=(64,2))
	valor = fields.Float(string='Valor', digits=(64,2))
	valuation_account_id = fields.Many2one('account.account',string=u'Cuenta Producto')
	input_account_id = fields.Many2one('account.account',string=u'Cuenta Variación')
	output_account_id = fields.Many2one('account.account',string=u'Cuenta Costo de Venta')