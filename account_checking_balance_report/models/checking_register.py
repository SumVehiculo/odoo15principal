# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools

class CheckingRegister(models.Model):
	_name = 'checking.register'
	_description = 'Checking Register'
	_auto = False

	mayor = fields.Char(string='Mayor')
	cuenta = fields.Char(string='Cuenta')
	nomenclatura = fields.Char(string='Nomenclatura')
	debe = fields.Float(string='Debe')
	haber = fields.Float(string='Haber')
	saldo_deudor = fields.Float(string='Saldo Deudor')
	saldo_acreedor = fields.Float(string='Saldo Acreedor')
	rubro = fields.Char(string='Rubro Estado Financiero')

	def init(self):
		tools.drop_view_if_exists(self.env.cr, self._table)
		self.env.cr.execute('''
			CREATE OR REPLACE VIEW %s AS (
				SELECT row_number() OVER () AS id, T.* FROM (select 
			left(a2.code,2) as mayor,
			a2.code as cuenta,
			a2.name as nomenclatura,
			a1.debe,
			a1.haber,
			case when a1.debe > a1.haber then a1.debe-a1.haber else  0 end as saldo_deudor,
			case when a1.haber> a1.debe then a1.haber-a1.debe else 0 end as saldo_acreedor,
			ati.name as rubro
			from get_sumas_mayor_f1('2019/01/01','2019/01/01',1,TRUE) a1
			left join account_account a2 on a2.id=a1.account_id
			left join account_type_it ati on ati.id = a2.account_type_it_id
			order by a2.code)T
				limit 1
			
			)''' % (self._table,)
		)