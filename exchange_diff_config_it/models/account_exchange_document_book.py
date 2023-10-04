# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountExchangeDocumentBook(models.Model):
	_name = 'account.exchange.document.book'
	_auto = False
	
	periodo = fields.Text(string='Periodo', size=50)
	cuenta = fields.Char(string='Cuenta')
	partner = fields.Char(string='Partner', size=150)
	td_sunat = fields.Char(string='TD', size=3)
	nro_comprobante = fields.Char(string='Nro. Comprobante', size=3)
	debe = fields.Float(string='Debe',digits=(12,2))
	haber = fields.Float(string='Haber',digits=(12,2))
	saldomn = fields.Float(string='Saldo MN',digits=(12,2))
	saldome = fields.Float(string='Saldo ME',digits=(12,2))
	tc = fields.Float(string='TC',digits=(12,3))
	saldo_act = fields.Float(string='Saldo Act.',digits=(12,2))
	diferencia = fields.Float(string='Diferencia',digits=(12,2))
	cuenta_diferencia = fields.Char(string='Cuenta Diferencia')
	account_id = fields.Many2one('account.account',string='Cuenta ID')
	partner_id = fields.Many2one('res.partner',string='Partner ID')
	period_id = fields.Many2one('account.period',string='Periodo ID')