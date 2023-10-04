# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountBookDiaryView(models.Model):
	_name = 'account.book.diary.view'
	_auto = False
	
	periodo = fields.Char(string='Periodo')
	fecha = fields.Date(string='Fecha')
	libro = fields.Char(string='Libro')
	voucher = fields.Char(string='Voucher')
	cuenta = fields.Char(string='Cuenta')
	debe = fields.Float(string='Debe', digits=(64,2))
	haber = fields.Float(string='Haber', digits=(64,2))
	balance = fields.Float(string='Balance', digits=(12,2))
	moneda = fields.Char(string='Mon')
	tc = fields.Float(string='TC', digits=(12,4))
	importe_me = fields.Float(string='Importe Me',digits=(64,2))
	cta_analitica = fields.Char(string='Cta Analítica')
	glosa = fields.Char(string='Glosa')
	td_partner = fields.Char(string='TDP')
	doc_partner = fields.Char(string='RUC')
	partner = fields.Char(string='Partner')
	td_sunat = fields.Char(string='TD')
	nro_comprobante = fields.Char(string=u'Nro Comp')
	fecha_doc = fields.Date(string=u'Fecha Doc')
	fecha_ven = fields.Date(string='Fecha Ven')
	col_reg = fields.Char(string='Col Reg')
	monto_reg = fields.Float(string='Monto Reg',digits=(12,3))
	medio_pago = fields.Char(string='Medio Pago')
	ple_diario = fields.Char(string='PLE Diario')
	ple_compras = fields.Char(string='PLE Compras')
	ple_ventas = fields.Char(string='PLE Ventas')