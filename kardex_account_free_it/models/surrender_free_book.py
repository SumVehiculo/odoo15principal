# -*- coding: utf-8 -*-

from odoo import models, fields, api

class SurrenderFreeBook(models.Model):
	_name = 'surrender.free.book'
	_auto = False
	
	fecha = fields.Date(string=u'Fecha')
	doc = fields.Char(string='Documento')
	producto = fields.Char(string=u'Producto')
	cantidad = fields.Float(string='Cantidad', digits=(64,2))
	valor = fields.Float(string='Valor', digits=(64,2))
	almacen = fields.Char(string=u'Almacén')
	origen = fields.Char(string=u'Origen')
	destino = fields.Char(string=u'Destino')
	concepto = fields.Char(string=u'Concepto')
	expense_account_id = fields.Many2one('account.account',string=u'Cuenta Gasto')
	valuation_account_id = fields.Many2one('account.account',string=u'Cuenta Producto')