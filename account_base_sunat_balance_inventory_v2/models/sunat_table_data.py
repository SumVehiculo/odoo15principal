# -*- coding: utf-8 -*-

from odoo import models, fields, api

class SunatTableData38(models.Model):
	_name = 'sunat.table.data.38'

	name = fields.Char(string=u'Denominación',required=True)
	date = fields.Date(string='Fecha')
	partner_id = fields.Many2one('res.partner',string=u'Emisor',required=True)
	amount = fields.Float(string='Valor Nominal',digits=(64,2))
	qty= fields.Float(string='Cantidad',digits=(64,2))
	total_cost = fields.Float(string='Costo Total',digits=(64,2))
	prov_total = fields.Float(string=u'Provisión Total',digits=(64,2))
	total = fields.Float(string='Total Neto',digits=(64,2))
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)

class SunatTableData39(models.Model):
	_name = 'sunat.table.data.39'

	name = fields.Char(string=u'Descripción del intagible',required=True)
	date = fields.Date(string='Fecha de inicio de la operación')
	type = fields.Char(string='Tipo de Intangible (Tabla 7)')
	amount = fields.Float(string='Valor Contable del Intangible',digits=(64,2))
	amort_acum = fields.Float(string='Amortización Contable Acumulada',digits=(64,2))
	total = fields.Float(string='Valor Neto Contable del Intangible',digits=(64,2))
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)