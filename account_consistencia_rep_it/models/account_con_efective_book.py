# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools

class AccountConEfectiveBook(models.Model):
	_name = 'account.con.efective.book'
	_description = 'Account Con Efective Book'
	_auto = False
	
	account_code = fields.Char(string='Cuenta')
	account_efective_type_name = fields.Char(string='Tipo Flujo de Efectivo')
	ingreso = fields.Float(string='Ingreso', digits=(64,2))
	egreso = fields.Float(string='Egreso', digits=(64,2))
	balance = fields.Float(string='Balance', digits=(64,2))

	def init(self):
		tools.drop_view_if_exists(self.env.cr, self._table)
		self.env.cr.execute('''
			CREATE OR REPLACE VIEW %s AS (
				SELECT row_number() OVER () AS id,
				vst_d.cuenta AS account_code,
				''::character varying AS account_efective_type_name,
				0::numeric as ingreso,
				0::numeric as egreso, 
				0::numeric as balance 
				FROM get_diariog('2019/01/01','2019/01/01',1) vst_d limit 1
			)''' % (self._table,)
		)