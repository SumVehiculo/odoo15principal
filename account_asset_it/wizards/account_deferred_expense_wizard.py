# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError
import base64

class AccountDeferredExpenseWizard(models.TransientModel):
	_name = 'account.deferred.expense.wizard'

	name = fields.Char()
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	fiscal_year_id = fields.Many2one('account.fiscal.year',string=u'Ejercicio',required=True)
	type_show = fields.Selection([('pantalla','Pantalla'),('excel','Excel')],string=u'Mostrar en',default='pantalla', required=True)

	def get_report(self):
		if self.type_show == 'excel':
			return self.get_excel()
		else:
			self.env.cr.execute("""
			DROP VIEW IF EXISTS account_deferred_expense_view;
			CREATE OR REPLACE view account_deferred_expense_view as (SELECT row_number() OVER () AS id, T.* FROM ("""+self.get_sql()+""")T)""")

			return {
				'name': 'Reporte Gastos Diferidos',
				'type': 'ir.actions.act_window',
				'res_model': 'account.deferred.expense.view',
				'view_mode': 'tree,pivot',
				'view_type': 'form',
			}

	def get_excel(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']

		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'Gastos.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		worksheet = workbook.add_worksheet("GASTOS DIFERIDOS")
		worksheet.set_tab_color('blue')

		HEADERS = ['FECHA','TD','COMPROBANTE','PROVEEDOR','MONTO SEGURO']
		periods = self.arr_periods(int(self.fiscal_year_id.date_from.strftime('%Y%m')),int(self.fiscal_year_id.date_to.strftime('%Y%m')))
		for p in periods:
			HEADERS.append(p)
		HEADERS.append('TOTAL DEVENGADO')
		HEADERS.append('POR DIFERIR')
		worksheet = ReportBase.get_headers(worksheet,HEADERS,0,0,formats['boldbord'])
		x=1
		self.env.cr.execute(self._get_sql_dynamic())
		res = self.env.cr.dictfetchall()

		for line in res:
			worksheet.write(x,0,line['invoice_date'] if line['invoice_date'] else '',formats['dateformat'])
			worksheet.write(x,1,line['td'] if line['td'] else '',formats['especial1'])
			worksheet.write(x,2,line['ref'] if line['ref'] else '',formats['especial1'])
			worksheet.write(x,3,line['partner'] if line['partner'] else '',formats['especial1'])
			worksheet.write(x,4,line['original_value'] if line['original_value'] else '0.00',formats['numberdos'])
			c = 5
			for i in periods:
				worksheet.write(x,c,line[i] if line[i] else 0,formats['numberdos'])
				c+=1
			worksheet.write(x,c,line['total_dev'] if line['total_dev'] else '0.00',formats['numberdos'])
			worksheet.write(x,c+1,line['amount_dif'] if line['amount_dif'] else '0.00',formats['numberdos'])
			x += 1

		widths = [15,8,20,30,20]
		siz_per = []
		for i in periods:
			siz_per.append(12)
		siz_per.append(21)
		siz_per.append(20)
		worksheet = ReportBase.resize_cells(worksheet,widths+siz_per)
		workbook.close()

		f = open(direccion +'Gastos.xlsx', 'rb')
		return self.env['popup.it'].get_file('Gastos Diferidos.xlsx',base64.encodebytes(b''.join(f.readlines())))
	
	def _get_sql_dynamic(self):
		sql_p = ""
		periods = self.arr_periods(int(self.fiscal_year_id.date_from.strftime('%Y%m')),int(self.fiscal_year_id.date_to.strftime('%Y%m')))
		for i in periods:
			sql_p += """, sum(CASE WHEN T.periodo = '%s' THEN T.amount_total ELSE 0 END) AS "%s" """%(i,i)
		sql = """select  T.invoice_date, T.td, T.ref, T.partner, T.original_value 
		 %s , sum(T.amount_total) as total_dev, T.original_value - sum(T.amount_total) as amount_dif
		from (select ai.invoice_date, ei.name as td,
			ai.ref,
			rp.name as partner,
			ass.original_value,
			to_char(am.date::timestamp with time zone, 'yyyymm'::text)::character varying as periodo,
			am.amount_total,
			ass.id as asset_id
			from account_move am
			left join account_asset ass on ass.id = am.asset_id
			left join account_move ai on ai.id = ass.invoice_id_it
			left join res_partner rp on rp.id = ai.partner_id
			left join l10n_latam_document_type ei on ei.id = ai.l10n_latam_document_type_id
			where am.asset_id is not null and ass.asset_type = 'expense' and (am.date between '%s' and '%s') 
			and ass.company_id = %d)T
			GROUP BY T.asset_id, T.invoice_date, T.td, T.ref, T.partner, T.original_value
		""" % (sql_p,self.fiscal_year_id.date_from.strftime('%Y/%m/%d'),
			self.fiscal_year_id.date_to.strftime('%Y/%m/%d'),
			self.company_id.id)
		
		return sql

	def arr_periods(self,ini,fin):
		arrr = [str(ini)]
		c = ini

		while (c != fin):
			if (str(c)[4:] != '12'):
				c += 1
			else:
				c = int(str(int(str(c)[:4])+1) + '01')
			arrr.append(str(c))
		arrr.append(str(fin))
		return arrr
	
	def get_sql(self):
		sql = """select ai.invoice_date,
			rp.name as partner, ass.acquisition_date, aj.name as diario, am.name as asiento,
			case when am.state = 'draft' then 'Borrador'
			when am.state = 'cancel' then 'Cancelado'
			when am.state = 'posted' then 'Publicado' end as estado,
			am.glosa, am.ref, am.date,
			am.amount_total
			from account_move am
			left join account_asset ass on ass.id = am.asset_id
			left join account_move ai on ai.id = ass.invoice_id_it
			left join res_partner rp on rp.id = ai.partner_id
			left join account_journal aj on aj.id = am.journal_id
			where am.asset_id is not null and ass.asset_type = 'expense' and (am.date between '%s' and '%s') 
			and ass.company_id = %d
		""" % (self.fiscal_year_id.date_from.strftime('%Y/%m/%d'),
			self.fiscal_year_id.date_to.strftime('%Y/%m/%d'),
			self.company_id.id)
		return sql