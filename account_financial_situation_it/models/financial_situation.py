# -*- coding: utf-8 -*-

from odoo import models, fields, api

class FinancialSituation(models.Model):
	_name = 'financial.situation'
	_auto = False
	_order = 'order_balance'

	name = fields.Char(string='Nombre')
	group_balance = fields.Char(string='Grupo')
	total = fields.Float(string='Total')
	order_balance = fields.Integer(string='Orden')