# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ConsumptionAnalysisBook(models.Model):
	_name = 'consumption.analysis.book'
	_auto = False
	
	almacen = fields.Char(string=u'Almacén')
	producto = fields.Char(string=u'Producto')
	analytic_account_id = fields.Many2one('account.analytic.account',string=u'Cuenta Analítica')
	analytic_tag_id = fields.Many2one('account.analytic.tag', string=u'Etiqueta Analítica')
	cantidad = fields.Float(string='Cantidad', digits=(64,2))
	valor = fields.Float(string='Valor', digits=(64,2))
	valuation_account_id = fields.Many2one('account.account',string=u'Cuenta Producto')
	input_account_id = fields.Many2one('account.account',string=u'Cuenta Variación')