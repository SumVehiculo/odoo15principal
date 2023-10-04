# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools

class EfectiveFlow(models.Model):
	_name = 'efective.flow'
	_description = 'Efective Flow'
	_auto = False
	_order = 'efective_order'

	name = fields.Char(string='Nombre')
	efective_group = fields.Char(string='Grupo')
	total = fields.Float(string='Total')
	efective_order = fields.Integer(string='Orden')

	def init(self):
		tools.drop_view_if_exists(self.env.cr, self._table)
		self.env.cr.execute('''
			CREATE OR REPLACE VIEW %s AS (
				SELECT row_number() OVER () AS id,
			*
			from get_efective_flow('201901','201901','201900',1) limit 1
			
			)''' % (self._table,)
		)