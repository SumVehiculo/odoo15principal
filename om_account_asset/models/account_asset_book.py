# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools

class AccountAssetBook(models.Model):
	_name = 'account.asset.book'
	_description = 'Account Asset Book'
	_auto = False
	
	code = fields.Char(string='Codigo', size=50)
	name = fields.Char(string='Activo', size=150)
	mes = fields.Integer(string='Mes')
	period = fields.Char(string='Periodo')
	cat_name = fields.Char(string=u'Categoría', size=100)
	cta_analitica = fields.Char(string='Cta. Analitica')
	eti_analitica = fields.Char(string='Etiqueta Analitica')
	cta_activo = fields.Char(string='Cta. Activo')
	cta_gasto = fields.Char(string='Cta. Gasto')
	cta_depreciacion = fields.Char(string='Cta Depreciacion')
	valor_dep = fields.Float(string=u'Valor de Depreciación',digits=(12,2))

	def init(self):
		tools.drop_view_if_exists(self.env.cr, self._table)
		self.env.cr.execute('''
			CREATE OR REPLACE VIEW %s AS (
				select row_number() OVER () AS id,
				''::character varying as code,
				''::character varying as name,
				line.sequence as mes,
				to_char(line.depreciation_date::timestamp with time zone, 'mm/yyyy'::text)::character varying as period,
				''::character varying as cat_name,
				''::character varying as cta_analitica,
				''::character varying as eti_analitica,
				''::character varying as cta_activo,
				''::character varying as cta_gasto,
				''::character varying as cta_depreciacion,
				0::numeric as valor_dep
				from account_asset_depreciation_line line limit 1
			
			)''' % (self._table,)
		)