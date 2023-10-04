# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.tools.misc import formatLang, format_date, get_lang

class AccountBalancePeriodUSDBook(models.Model):
	_name = 'account.balance.period.usd.book'
	_auto = False
	
	periodo = fields.Text(string='Periodo', size=50)
	fecha_con = fields.Date(string='Fecha Con')
	libro = fields.Char(string='Libro', size=5)
	voucher = fields.Char(string='Voucher', size=10)
	td_partner = fields.Char(string='TDP', size=50)
	doc_partner = fields.Char(string='RUC',size=50)
	partner = fields.Char(string='Partner')
	td_sunat = fields.Char(string='TD',size=3)
	nro_comprobante = fields.Char(string='Nro Comp', size=50)
	fecha_doc = fields.Date(string='Fecha Doc')
	fecha_ven = fields.Date(string='Fecha Ven')
	cuenta = fields.Char(string='Cuenta')
	moneda = fields.Char(string='Moneda')
	debe = fields.Float(string='Debe', digits=(64,2))
	haber = fields.Float(string='Haber', digits=(64,2))
	saldo_mn = fields.Float(string='Saldo Mn', digits=(64,2))
	saldo_me = fields.Float(string='Saldo Me', digits=(64,2))
	aml_ids = fields.Text('Detalle')
	partner_id = fields.Many2one('res.partner',string='Partner')
	account_id = fields.Many2one('account.account',string='Cuenta')
	move_id = fields.Many2one('account.move',string='Factura')

	def edit_linea_it(self):
		arr = str(self.aml_ids)
		arr2 = arr.replace(']','').replace('[','')
		t = arr2.split(',')

		elem = []
		for i in t:
			if i!= 0:
				elem.append(i)

		return {
			'name': 'Detalle',
			'domain' : [('id','in',elem)],
			'type': 'ir.actions.act_window',
			'res_model': 'account.move.line',
			'view_mode': 'tree',
			'view_type': 'form',
			'views': [(False, 'tree')],
			'target': '_blank',
		}