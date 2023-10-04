# -*- coding: utf-8 -*-

from odoo import models, fields, api

class KardexEntryIncomeBook(models.Model):
	_name = 'kardex.entry.income.book'
	
	fecha = fields.Date(string=u'Fecha')
	tipo = fields.Char(string=u'Tipo')
	serie = fields.Char(string=u'Serie')
	numero = fields.Char(string=u'Número')
	doc_almacen = fields.Char(string=u'Doc. Almacén')
	ruc = fields.Char(string=u'RUC')
	empresa = fields.Char(string=u'Empresa')
	tipo_op = fields.Char(string=u'T. OP.')
	tipo_name = fields.Char(string=u'Nombre T. OP.')
	producto = fields.Char(string=u'Producto')
	default_code = fields.Char(string=u'Código Producto')
	unidad = fields.Char(string=u'Unidad')
	qty = fields.Float(string=u'Cantidad',digits=(64,2))
	amount = fields.Float(string=u'Costo',digits=(64,6))
	cta_debe = fields.Many2one('account.account',string=u'Cuenta Debe')
	cta_haber = fields.Many2one('account.account',string=u'Cuenta Haber')
	origen = fields.Char(string=u'Ubicación Origen')
	destino = fields.Char(string=u'Ubicación Destino')
	almacen = fields.Char(string=u'Almacén')
	analytic_account_id = fields.Many2one('account.analytic.account',string=u'Cuenta Analítica')