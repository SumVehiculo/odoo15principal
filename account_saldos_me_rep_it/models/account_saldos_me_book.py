# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountSaldosMeBook(models.Model):
	_name = 'account.saldos.me.book'
	_auto = False

	cuenta = fields.Char(string='Cuenta', size=64)
	denominacion = fields.Char(string='Denominacion')
	moneda = fields.Char(string='Moneda', size=5)
	debe = fields.Float(string='Debe MN', digits=(64,2))
	haber = fields.Float(string='Haber MN', digits=(64,2))
	saldo = fields.Float(string='Saldo MN', digits=(12,2))
	debe_me = fields.Float(string='Debe ME', digits=(64,2))
	haber_me = fields.Float(string='Haber ME', digits=(64,2))
	saldo_me = fields.Float(string='Saldo ME', digits=(12,2))