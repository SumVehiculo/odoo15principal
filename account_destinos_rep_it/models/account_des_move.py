# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountDesMove(models.Model):
	_name = 'account.des.move'
	_auto = False
	
	periodo = fields.Char(string='Periodo')
	fecha = fields.Date(string='Fecha')
	libro = fields.Char(string='Libro', size=5)
	voucher = fields.Char(string='Voucher', size=10)
	cuenta = fields.Char(string='Cuenta', size=64)
	debe = fields.Float(string='Debe', digits=(64,2))
	haber = fields.Float(string='Haber', digits=(64,2))
	balance = fields.Float(string='Balance', digits=(12,2))
	cta_analitica = fields.Char(string=u'Cuenta Analítica')
	des_debe = fields.Char(string=u'Dest Debe') 
	des_haber = fields.Char(string=u'Dest Haber')
