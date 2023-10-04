# -*- coding: utf-8 -*-

from odoo import models, fields, api

class FunctionResult(models.Model):
	_name = 'function.result'
	_auto = False
	_order = 'order_function'

	name = fields.Char(string='Nombre')
	group_function = fields.Char(string='Grupo')
	total = fields.Float(string='Total')
	order_function = fields.Integer(string='Orden')