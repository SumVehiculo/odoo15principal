# -*- coding: utf-8 -*-

from odoo import models, fields, api

class NatureResult(models.Model):
	_name = 'nature.result'
	_auto = False
	_order = 'order_nature'

	name = fields.Char(string='Nombre')
	group_nature = fields.Char(string='Grupo')
	total = fields.Float(string='Total')
	order_nature = fields.Integer(string='Orden')