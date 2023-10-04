# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools

class AccountBankBook(models.Model):
	_name = 'account.bank.book'
	_description = 'Account Bank Book'
	_auto = False
	
	fecha = fields.Date(string='Fecha')
	partner = fields.Char(string='Partner')
	documento = fields.Char(string='Documento')
	glosa = fields.Char(string='Glosa')
	cargomn = fields.Float(string='Cargo MN',digits=(64,2))
	abonomn = fields.Float(string='Abono MN',digits=(64,2))
	saldomn = fields.Float(string='Saldo MN',digits=(64,2))
	cargome = fields.Float(string='Cargo ME',digits=(64,2))
	abonome = fields.Float(string='Abono ME',digits=(64,2))
	saldome = fields.Float(string='Saldo ME',digits=(64,2))
	asiento = fields.Char(string='Nro Asiento')

	def init(self):
		tools.drop_view_if_exists(self.env.cr, self._table)
		self.env.cr.execute('''
			CREATE OR REPLACE VIEW %s AS (
				SELECT 
				row_number() OVER () AS id,
				fecha,partner,nro_comprobante as documento,glosa,debe AS cargomn,haber AS abonomn,
				0::numeric AS saldomn,
				0::numeric AS cargome,
				0::numeric AS abonome,
				0::numeric AS saldome,
				voucher as asiento
				from get_mayorg('2019/01/01','2019/01/31',1,'{1,2}') a limit 1
			
			)''' % (self._table,)
		)