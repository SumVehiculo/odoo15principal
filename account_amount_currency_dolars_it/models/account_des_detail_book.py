# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountDesDetailUSDBook(models.Model):
	_name = 'account.des.detail.usd.book'
	_auto = False
	
	periodo = fields.Text(string='Periodo', size=50)
	fecha = fields.Text(string='Fecha', size=15)
	libro = fields.Char(string='Libro', size=5)
	voucher = fields.Char(string='Voucher', size=10)
	mayorf = fields.Char(string='Mayor F', size=64)
	mayord = fields.Char(string='Mayor D', size=64)
	cuenta = fields.Char(string='Cuenta', size=64)
	debe = fields.Float(string='Debe', digits=(64,2))
	haber = fields.Float(string='Haber', digits=(64,2))
	balance = fields.Float(string='Balance', digits=(12,2))
	debe_me = fields.Float(string='Debe ME', digits=(64,2))
	haber_me = fields.Float(string='Haber ME', digits=(64,2))
	balance_me = fields.Float(string='Balance ME', digits=(12,2))
	cta_analitica = fields.Char(string=u'Cuenta Analítica')
	des_debe = fields.Char(string=u'Dest Debe') 
	des_haber = fields.Char(string=u'Dest Haber')
