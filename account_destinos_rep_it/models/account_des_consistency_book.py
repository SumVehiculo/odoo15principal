# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountDesConsistencyBook(models.Model):
	_name = 'account.des.consistency.book'
	_auto = False
	
	periodo = fields.Char(string='Periodo')
	libro = fields.Char(string='Libro', size=5)
	voucher = fields.Char(string='Voucher', size=10)
	cuenta = fields.Char(string='Cuenta', size=64)
	debe = fields.Float(string='Debe', digits=(64,2))
	haber = fields.Float(string='Haber', digits=(64,2))
