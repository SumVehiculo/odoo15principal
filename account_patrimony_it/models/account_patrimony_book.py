# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountPatrimonyBook(models.Model):
	_name = 'account.patrimony.book'
	_auto = False
	
	glosa = fields.Char(string='Conceptos')
	capital = fields.Float(string='Capital', digits=(64,2))
	acciones = fields.Float(string='Acciones de Inversion', digits=(64,2))
	cap_add = fields.Float(string='Capital Adicional', digits=(64,2))
	res_no_real = fields.Float(string='Resultados no Realizados', digits=(64,2))
	exce_de_rev = fields.Float(string='Excedente de Revaluacion', digits=(64,2))
	reservas = fields.Float(string='Reservas', digits=(64,2))
	res_ac = fields.Float(string='Resultados Acumulados', digits=(64,2))
	total = fields.Float(string='Totales', digits=(64,2))