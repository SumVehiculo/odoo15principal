# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools

class AccountAsset71Book(models.Model):
	_name = 'account.asset.74.book'
	_description = 'Account Asset 74 Book'
	_auto = False
	
	campo1 = fields.Char(string=u'Activo Fijo')
	campo2 = fields.Date(string=u'Fecha del Contrato')
	campo3 = fields.Char(string=u'Nro del Contrato de Arrendamiento')
	campo4 = fields.Date(string=u'Fecha del Inicio del Contrato')
	campo5 = fields.Integer(string=u'Nro de Cuotas Pactadas')
	campo6 = fields.Float(string=u'Monto del Contrato',digits=(12,2))

	def init(self):
		tools.drop_view_if_exists(self.env.cr, self._table)
		self.env.cr.execute('''
			CREATE OR REPLACE VIEW %s AS (
				SELECT row_number() OVER () AS id,
				name as campo1, 
				contract_date as campo2, 
				contract_number as campo3,
				date_start_contract as campo4,
				fees_number as campo5, 
				amount_total_contract as campo6 
				from account_asset_asset limit 1
			
			)''' % (self._table,)
		)