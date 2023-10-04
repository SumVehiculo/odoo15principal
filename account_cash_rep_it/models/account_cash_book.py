# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools

class AccountCashBook(models.Model):
	_name = 'account.cash.book'
	_description = 'Account Cash Book'
	_auto = False
	
	periodo = fields.Text(string='Periodo', size=50)
	fecha = fields.Text(string='Fecha', size=15)
	libro = fields.Char(string='Libro', size=5)
	voucher = fields.Char(string='Voucher', size=10)
	cuenta = fields.Char(string='Cuenta', size=64)
	debe = fields.Float(string='Debe', digits=(64,2))
	debe_me = fields.Float(string='Debe ME', digits=(64,2))
	haber = fields.Float(string='Haber', digits=(64,2))
	haber_me = fields.Float(string='Haber ME', digits=(64,2))
	saldo = fields.Float(string='Saldo Mn', digits=(64,2))
	moneda = fields.Char(string='Moneda', size=5)
	tc = fields.Float(string='Tipo Cambio', digits=(12,4))
	saldo_me = fields.Float(string='Saldo Me', digits=(64,2))
	cta_analitica = fields.Char(string='Cuenta Analítica')
	glosa = fields.Char(string='Glosa',size=50)
	td_partner = fields.Char(string='Tipo de Documento', size=50)
	doc_partner = fields.Char(string='RUC')
	partner = fields.Char(string='Partner')
	td_sunat = fields.Char(string='Tipo Documento Sunat',size=50)
	nro_comprobante = fields.Char(string=u'Número de Comprobante', size=50)
	fecha_doc = fields.Date(string=u'Fecha Documento')
	fecha_ven = fields.Date(string='Fecha Vencimiento')

	def init(self):
		tools.drop_view_if_exists(self.env.cr, self._table)
		self.env.cr.execute('''
			CREATE OR REPLACE VIEW %s AS (
				select row_number() OVER () AS id,
				periodo::text, fecha, libro, voucher, cuenta,
				debe, haber,saldo, moneda, tc, debe_me, haber_me, saldo_me,
				cta_analitica, glosa, td_partner,doc_partner, partner, 
				td_sunat,nro_comprobante, fecha_doc, fecha_ven
				from get_mayorg('2019/01/01','2019/01/31',1,'{1,2}')
				limit 1
			
			)''' % (self._table,)
		)
