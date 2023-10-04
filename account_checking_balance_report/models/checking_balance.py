# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools

class CheckingBalance(models.Model):
	_name = 'checking.balance'
	_description = 'Checking Balance'
	_auto = False

	cuenta = fields.Char(string='Mayor')
	nomenclatura = fields.Char(string='Nomenclatura')
	debe = fields.Float(string='Debe')
	haber = fields.Float(string='Haber')
	saldo_deudor = fields.Float(string='Saldo Deudor')
	saldo_acreedor = fields.Float(string='Saldo Acreedor')

	def init(self):
		tools.drop_view_if_exists(self.env.cr, self._table)
		self.env.cr.execute('''
			CREATE OR REPLACE VIEW %s AS (
			SELECT row_number() OVER () AS id, T.* FROM (select 
			a2.code_prefix_start as cuenta,
			a2.name as nomenclatura,
			a1.debe,
			a1.haber,
			case when a1.debe > a1.haber then a1.debe-a1.haber else  0 end as saldo_deudor,
			case when a1.haber> a1.debe then a1.haber-a1.debe else 0 end as saldo_acreedor
			from get_sumas_balance_f1('2019/01/01','2019/01/01',1,TRUE) a1
			left join account_group a2 on a2.id=a1.account_id
			order by a2.code_prefix_start)T
				limit 1
			
			)''' % (self._table,)
		)