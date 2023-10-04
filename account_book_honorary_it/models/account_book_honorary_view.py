# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools

class AccountBookHonoraryView(models.Model):
	_name = 'account.book.honorary.view'
	_description = 'Account Book Honorary View'
	_auto = False
	
	periodo = fields.Text(string='Periodo', size=50)
	libro = fields.Char(string='Libro', size=5)
	voucher = fields.Char(string='Voucher', size=10)
	fecha_e = fields.Date(string='Fecha E')
	fecha_p = fields.Date(string='Fecha P')
	td = fields.Char(string='TD',size=3)
	serie = fields.Text(string='Serie', size=50)
	numero = fields.Text(string='Numero', size=50)
	tdp = fields.Char(string='TDP', size=50)
	docp = fields.Char(string='RUC',size=50)
	apellido_p = fields.Char(string='Ap. Paterno')
	apellido_m = fields.Char(string='Ap. Materno')
	namep = fields.Char(string='Nombres')
	divisa = fields.Char(string='Divisa')
	tipo_c = fields.Float(string='TC',digits=(12,4))
	renta = fields.Float(string='Renta',digits=(12,2))
	retencion = fields.Float(string='Retencion',digits=(12,2))
	neto_p = fields.Float(string='Neto P',digits=(12,2))
	periodo_p = fields.Text(string='Periodo P', size=50)
	is_not_home = fields.Char(string='No Domiciliado',size=1)
	c_d_imp = fields.Char(string='Conv. Evit. Doble Imp.')

	#def init(self):
	#	tools.drop_view_if_exists(self.env.cr, self._table)
	#	self.env.cr.execute('''
	#		CREATE OR REPLACE VIEW %s AS (
	#			select row_number() OVER () AS id,
	#				periodo, fecha_cont, libro, voucher, fecha_e, fecha_v, td, 
	#				serie, anio, numero, tdp, docp, namep, exp, venta_g, inaf, exo, isc_v, icbper,
	#				otros_v, igv_v, total, name, monto_me, currency_rate, fecha_det, 
	#				comp_det, f_doc_m, td_doc_m, serie_m, numero_m, glosa
	#				from vst_ventas_1_1 limit 1
	#		
	#		)''' % (self._table,)
	#	)