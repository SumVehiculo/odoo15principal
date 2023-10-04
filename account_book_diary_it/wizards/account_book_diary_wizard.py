# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import date
from odoo.exceptions import UserError
import base64
from io import BytesIO
import re
import uuid


class AccountBookDiaryWizard(models.TransientModel):
	_name = 'account.book.diary.wizard'

	name = fields.Char()
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	fiscal_year_id = fields.Many2one('account.fiscal.year',string=u'Ejercicio',required=True)
	date_from = fields.Date(string=u'Fecha Inicial')
	date_to = fields.Date(string=u'Fecha Final')
	period_from_id = fields.Many2one('account.period',string='Periodo Inicial')
	period_to_id = fields.Many2one('account.period',string='Periodo Final')
	type_show = fields.Selection([('pantalla','Pantalla'),('excel','Excel'),('csv','CSV')],string=u'Mostrar en',default='pantalla', required=True)
	show_by = fields.Selection([('date','Fechas'),('period','Periodos')],string='Mostrar en base a',default='date')
	content = fields.Selection([('all','Todos los diarios'),('pick','Escoger diarios')],string='Contenido',default='all')
	journal_ids = fields.Many2many('account.journal',string=u'Libros')

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
		sql_journals = ""
		if self.content == 'pick':
			if not self.journal_ids:
				raise UserError(u'Debe escoger por lo menos un Diario.')
			sql_journals = "WHERE am.journal_id in (%s) " % (','.join(str(i) for i in self.journal_ids.ids))

		sql = """SELECT
			vst1.periodo::character varying,vst1.fecha,vst1.libro,vst1.voucher,
			vst1.cuenta,vst1.debe,vst1.haber,vst1.balance,
			vst1.moneda,vst1.tc,vst1.importe_me,vst1.cta_analitica,
			vst1.glosa,vst1.td_partner,vst1.doc_partner,vst1.partner,
			vst1.td_sunat,vst1.nro_comprobante,vst1.fecha_doc,vst1.fecha_ven,
			vst1.col_reg,vst1.monto_reg,vst1.medio_pago,vst1.ple_diario,
			vst1.ple_compras,vst1.ple_ventas
			FROM get_diariog('%s','%s',%d) vst1
			LEFT JOIN account_move am on am.id =  vst1.move_id %s
		""" % (self.date_from.strftime('%Y/%m/%d') if self.show_by == 'date' else self.period_from_id.date_start.strftime('%Y/%m/%d'),
			self.date_to.strftime('%Y/%m/%d') if self.show_by == 'date' else self.period_to_id.date_end.strftime('%Y/%m/%d'),
			self.company_id.id,
			sql_journals)
		return sql

	def get_report(self):
		
		if self.type_show == 'pantalla':
			self.env.cr.execute("""
			DROP VIEW IF EXISTS account_book_diary_view;
			CREATE OR REPLACE view account_book_diary_view as (SELECT row_number() OVER () AS id, T.* FROM ("""+self._get_sql()+""")T)""")

			return {
				'name': 'Libro Diario',
				'type': 'ir.actions.act_window',
				'res_model': 'account.book.diary.view',
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
		return self.env['popup.it'].get_file('Libro Diario.xlsx',workbook)

	def getCsv(self):
		ReportBase = self.env['report.base']
		workbook = ReportBase.get_file_sql_export(self._get_sql(),',',True)
		return self.env['popup.it'].get_file('Libro Diario.csv',workbook)
	
	def get_header(self):
		HEADERS = ['PERIODO','FECHA','LIBRO','VOUCHER','CUENTA','DEBE','HABER','BALANCE','MON','TC','IMP ME',
		'CTA ANALITICA','GLOSA','TDP','RUC','PARTNER','TD','NRO COMP','FECHA DOC','FECHA VEN','COL REG','MONTO REG','MED PAGO',
		'PLE DIARIO','PLE COMPRAS','PLE VENTAS']
		return HEADERS