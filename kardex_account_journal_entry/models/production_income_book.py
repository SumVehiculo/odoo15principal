# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ProductionIncomeBook(models.Model):
	_name = 'production.income.book'
	_auto = False
	
	fecha = fields.Date(string='Fecha')
	tipo = fields.Char(string=u'Tipo')
	serie = fields.Char(string=u'Serie')
	numero = fields.Char(string=u'Numero')
	doc = fields.Char(string=u'Doc Almacén')
	ruc = fields.Char(string=u'RUC')
	empresa = fields.Char(string=u'Empresa')
	tipo_operacion = fields.Char(string=u'T. OP.')
	producto = fields.Char(string=u'Producto')
	codigo = fields.Char(string=u'Código')
	unidad = fields.Char(string=u'Unidad')
	cantidad = fields.Float(string='Cantidad', digits=(64,2))
	valor = fields.Float(string='Valor', digits=(64,2))
	categ_id = fields.Many2one('product.category',string=u'Categoría')
	valuation_account_id = fields.Many2one('account.account',string=u'Cuenta Valuación')
	input_account_id = fields.Many2one('account.account',string=u'Cuenta Entrada')
	almacen = fields.Char(string=u'Almacen')