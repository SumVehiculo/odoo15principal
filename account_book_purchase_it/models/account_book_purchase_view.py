# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools

class AccountBookPurchaseView(models.Model):
	_name = 'account.book.purchase.view'
	_description = 'Account Book Purchase View'
	_auto = False
	
	periodo = fields.Char(string='Periodo')
	fecha_cont = fields.Date(string='Fecha Cont')
	libro = fields.Char(string='Libro')
	voucher = fields.Char(string='Voucher')
	fecha_e = fields.Date(string='Fecha Em')
	fecha_v = fields.Date(string='Fecha Ven')
	td = fields.Char(string='TD',size=3)
	serie = fields.Char(string='Serie', size=50)
	anio = fields.Char(string=u'Año')
	numero = fields.Char(string='Numero', size=50)
	tdp = fields.Char(string='TDP', size=50)
	docp = fields.Char(string='RUC',size=50)
	namep = fields.Char(string='Partner')
	base1 = fields.Float(string='BIOGYE',digits=(12,2))
	base2 = fields.Float(string='BIOGEYNG',digits=(12,2))
	base3 = fields.Float(string='BIONG',digits=(12,2))
	cng = fields.Float(string='CNG',digits=(12,2))
	isc = fields.Float(string='ISC',digits=(12,2))
	icbper = fields.Float(string='ICBPER',digits=(12,2))
	otros = fields.Float(string='Otros',digits=(12,2))
	igv1 = fields.Float(string='IGV 1',digits=(12,2))
	igv2 = fields.Float(string='IGV 2',digits=(12,2))
	igv3 = fields.Float(string='IGV 3',digits=(12,2))
	total = fields.Float(string='Total',digits=(12,2))
	name = fields.Char(string='Mon')
	monto_me = fields.Float(string='Monto Me',digits=(12,2))
	currency_rate = fields.Float(string='TC',digits=(12,4))
	fecha_det = fields.Date(string='Fecha Det')
	comp_det = fields.Char(string='Comp Det')
	f_doc_m = fields.Date(string='Fecha Doc M')
	td_doc_m = fields.Char(string='TD Doc M')
	serie_m = fields.Char(string='Serie M')
	numero_m = fields.Char(string='Numero M')
	glosa = fields.Char(string='Glosa')

	#def init(self):
	#	tools.drop_view_if_exists(self.env.cr, self._table)
	#	self.env.cr.execute('''
	#		CREATE OR REPLACE VIEW %s AS (
	#			select row_number() OVER () AS id,
	#				periodo, fecha_cont, libro, voucher, fecha_e, fecha_v, td, 
	#				serie, anio, numero, tdp, docp, namep, exp, venta_g, inaf, exo, isc_v, icbper,
	#				otros_v, igv_v, total, name, monto_me, currency_rate, fecha_det, 
	#				comp_det, f_doc_m, td_doc_m, serie_m, numero_m, glosa
	#				from vst_compras_1_1 limit 1
	#		
	#		)''' % (self._table,)
	#	)