# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools

class AccountBookPerceptionSp(models.Model):
	_name = 'account.book.perception.sp'
	_description = 'Account Book Perception Sp'
	_auto = False

	periodo_con = fields.Char(string='Periodo Con', size=50)
	periodo_percep = fields.Char(string='Periodo Percep', size=50)
	fecha_uso = fields.Date(string='Fecha Uso')
	libro = fields.Char(string='Libro', size=5)
	voucher = fields.Char(string='Voucher', size=10)
	tipo_per = fields.Char(string='TDP',size=3)
	ruc_agente = fields.Char(string='RUC',size=50)
	partner = fields.Char(string='Partner')
	tipo_comp = fields.Char(string='TD')
	serie_cp = fields.Char(string='Serie', size=50)
	numero_cp = fields.Char(string='Numero', size=50)
	fecha_com_per = fields.Date(string='Fecha Com Per')
	percepcion = fields.Float(string='Percepcion',digits=(12,2))

	#def init(self):
	#	tools.drop_view_if_exists(self.env.cr, self._table)
	#	self.env.cr.execute('''
	#		CREATE OR REPLACE VIEW %s AS (
	#			select row_number() OVER () AS id,
	#			periodo_con, periodo_percep, fecha_uso, libro,
	#			voucher, tipo_per, ruc_agente, partner, tipo_comp, serie_cp, numero_cp,
	#			fecha_com_per, percepcion
	#			from get_percepciones_sp('2019/01/01','2019/01/31',1) limit 1
	#		
	#		)''' % (self._table,)
	#	)