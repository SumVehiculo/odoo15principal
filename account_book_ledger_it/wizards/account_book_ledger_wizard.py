# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import date
from odoo.exceptions import UserError
import base64
from io import BytesIO
import re
import uuid

class AccountBookLedgerWizard(models.TransientModel):
	_name = 'account.book.ledger.wizard'

	name = fields.Char()
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	fiscal_year_id = fields.Many2one('account.fiscal.year',string=u'Ejercicio',required=True)
	date_from = fields.Date(string=u'Fecha Inicial')
	date_to = fields.Date(string=u'Fecha Final')
	period_from_id = fields.Many2one('account.period',string='Periodo Inicial')
	period_to_id = fields.Many2one('account.period',string='Periodo Final')
	type_show = fields.Selection([('pantalla','Pantalla'),('excel','Excel'),('csv','CSV')],string=u'Mostrar en',default='pantalla', required=True)
	show_by = fields.Selection([('date','Fechas'),('period','Periodos')],string='Mostrar en base a',default='date')
	content = fields.Selection([('all','Todas las cuentas'),('pick','Escoger cuentas')],string='Contenido',default='all')
	account_ids = fields.Many2many('account.account',string=u'Cuentas')

	@api.onchange('company_id')
	def get_fiscal_year(self):
		if self.company_id:
			today = fields.Date.context_today(self)
			fiscal_year = self.env['account.fiscal.year'].search([('name','=',str(today.year))],limit=1)
			if fiscal_year:
				self.fiscal_year_id = fiscal_year.id
				self.date_from = fiscal_year.date_from
				self.date_to = fiscal_year.date_to

	def _get_sql(self):
		sql_accounts = "(select array_agg(id) from account_account where company_id = %d)"%(self.company_id.id)
		if self.content == 'pick':
			if not self.account_ids:
				raise UserError(u'Debe escoger por lo menos una Cuenta')
			sql_accounts = "array[%s] " % (','.join(str(i) for i in self.account_ids.ids))

		sql = """SELECT
			may.periodo::character varying,may.fecha,may.libro,may.voucher,
			may.cuenta,may.debe,may.haber,may.balance, may.saldo,
			may.moneda,may.tc,may.cta_analitica,
			may.glosa,may.td_partner,may.doc_partner,may.partner,
			may.td_sunat,may.nro_comprobante,may.fecha_doc,may.fecha_ven
			FROM get_mayorg('%s','%s',%d,%s) may
		""" % (self.date_from.strftime('%Y/%m/%d') if self.show_by == 'date' else self.period_from_id.date_start.strftime('%Y/%m/%d'),
			self.date_to.strftime('%Y/%m/%d') if self.show_by == 'date' else self.period_to_id.date_end.strftime('%Y/%m/%d'),
			self.company_id.id,
			sql_accounts)
		return sql

	def get_report(self):
		
		if self.type_show == 'pantalla':
			self.env.cr.execute("""
			DROP VIEW IF EXISTS account_book_ledger_view;
			CREATE OR REPLACE view account_book_ledger_view as (SELECT row_number() OVER () AS id, T.* FROM ("""+self._get_sql()+""")T)""")

			return {
				'name': u'Libro Mayor Analítico',
				'type': 'ir.actions.act_window',
				'res_model': 'account.book.ledger.view',
				'view_mode': 'tree,pivot,graph',
				'view_type': 'form',
			}

		if self.type_show == 'excel':
			return self.get_excel()
		
		if self.type_show == 'csv':
			return self.getCsv()

	def get_excel(self):
		ReportBase = self.env['report.base']
		workbook = ReportBase.get_excel_sql_export(self._get_sql(),self.get_header())
		return self.env['popup.it'].get_file(u'Libro Mayor Analítico.xlsx',workbook)

	def getCsv(self):
		ReportBase = self.env['report.base']
		workbook = ReportBase.get_file_sql_export(self._get_sql(),',',True)
		return self.env['popup.it'].get_file(u'Libro Mayor Analítico.csv',workbook)
	
	def get_header(self):
		HEADERS = ['PERIODO','FECHA','LIBRO','VOUCHER','CUENTA','DEBE','HABER','BALANCE','SALDO','MON','TC',
				   'CTA ANALITICA','GLOSA','TDP','RUC','PARTNER','TD','NRO COMPROBANTE','FECHA DOC','FECHA VEN']
		return HEADERS