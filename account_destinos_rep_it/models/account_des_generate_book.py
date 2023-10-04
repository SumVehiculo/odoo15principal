# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountDesGenerateBook(models.Model):
	_name = 'account.des.generate.book'
	_auto = False
	
	periodo = fields.Char(string='Periodo')
	glosa = fields.Text(string='Glosa')
	cuenta = fields.Char(string='Cuenta', size=64)
	name = fields.Char(string='Nomenclatura')
	debe = fields.Float(string='Debe', digits=(64,2))
	haber = fields.Float(string='Haber', digits=(64,2))
