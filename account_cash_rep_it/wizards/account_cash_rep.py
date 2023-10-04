# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError
import base64

class AccountCashRep(models.TransientModel):
	_name = 'account.cash.rep'
	_description = 'Account Cash Rep'

	name = fields.Char()
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	fiscal_year_id = fields.Many2one('account.fiscal.year',string=u'Ejercicio Fiscal',required=True)
	date_from = fields.Date(string=u'Fecha Inicial',required=True)
	date_to = fields.Date(string=u'Fecha Final',required=True)
	type_show =  fields.Selection([('pantalla','Pantalla'),('excel','Excel'),('csv','CSV')],string=u'Mostrar en', required=True, default='pantalla')
	account_ids = fields.Many2many('account.account','account_book_account_cash_rel','id_cash_origen','id_account_destino',string=u'Cuentas', required=True)
	show_header = fields.Boolean(string='Mostrar cabecera',default=False)

	@api.onchange('company_id')
	def get_fiscal_year(self):
		if self.company_id:
			today = fields.Date.context_today(self)
			fiscal_year = self.env['account.fiscal.year'].search([('name','=',str(today.year))],limit=1)
			if fiscal_year:
				self.fiscal_year_id = fiscal_year.id
				self.date_from = fiscal_year.date_from
				self.date_to = fiscal_year.date_to

	def get_report(self):
		self.domain_dates()
		if self.type_show == 'pantalla':
			self.env.cr.execute("""
			CREATE OR REPLACE view account_cash_book as (SELECT row_number() OVER () AS id, T.* FROM ("""+self._get_sql()+""")T)""")
			return {
				'name': 'Libro Caja Bancos',
				'type': 'ir.actions.act_window',
				'res_model': 'account.cash.book',
				'view_mode': 'tree',
				'view_type': 'form',
				'views': [(False, 'tree')],
			}

		if self.type_show == 'excel':
			return self.get_excel()
		
		if self.type_show == 'csv':
			return self.getCsv()
	
	def getCsv(self):
		ReportBase = self.env['report.base']
		workbook = ReportBase.get_file_sql_export(self._get_sql(),',',True)
		return self.env['popup.it'].get_file('LibroCajaBancos.csv',workbook)

	def _get_sql(self):
		sql_acc = "(select array_agg(id) from account_account where company_id = %d AND LEFT(code,2) = '10')"%(self.company_id.id)
		if self.account_ids:
			sql_acc = "'{%s}'" % (','.join(str(i) for i in self.account_ids.ids))
		sql = """
		select periodo::text, fecha, libro, voucher, cuenta,
		debe, haber,saldo, moneda, tc, debe_me, haber_me, saldo_me,
		cta_analitica, glosa, td_partner,doc_partner, partner, 
		td_sunat,nro_comprobante, fecha_doc, fecha_ven
		from get_mayorg('%s','%s',%d,%s)
		""" % (self.date_from.strftime('%Y/%m/%d'),
			self.date_to.strftime('%Y/%m/%d'),
			self.company_id.id,
			sql_acc)
		
		return sql

	def get_excel(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']

		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'LibroCajaBancos.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		##########LIBRO CAJA Y BANCOS############
		worksheet = workbook.add_worksheet("LIBRO CAJA Y BANCOS")
		worksheet.set_tab_color('blue')
		x=0
		if self.show_header:
			worksheet.merge_range(x,0,x,12, "LIBRO CAJA Y BANCOS", formats['especial5'] )
			x+=2
			worksheet.write(x,0,u"Compañía:",formats['especial2'])
			worksheet.merge_range(x,1,x,12,self.company_id.name,formats['especial2'])
			x+=1
			worksheet.write(x,0,"Fecha Inicial:",formats['especial2'])
			worksheet.merge_range(x,1,x,2,str(self.date_from),formats['especial2'])
			x+=1
			worksheet.write(x,0,"Fecha Final:",formats['especial2'])
			worksheet.merge_range(x,1,x,2,str(self.date_to),formats['especial2'])
			x+=2

		worksheet = ReportBase.get_headers(worksheet,self.get_header(),x,0,formats['boldbord'])
		self.env.cr.execute(self._get_sql())
		res = self.env.cr.dictfetchall()
		x+=1

		for line in res:
			worksheet.write(x,0,line['periodo'] if line['periodo'] else '',formats['especial1'])
			worksheet.write(x,1,line['fecha'] if line['fecha'] else '',formats['dateformat'])
			worksheet.write(x,2,line['libro'] if line['libro'] else '',formats['especial1'])
			worksheet.write(x,3,line['voucher'] if line['voucher'] else '',formats['especial1'])
			worksheet.write(x,4,line['cuenta'] if line['cuenta'] else '',formats['especial1'])
			worksheet.write(x,5,line['debe'] if line['debe'] else '0.00',formats['numberdos'])
			worksheet.write(x,6,line['haber'] if line['haber'] else '0.00',formats['numberdos'])
			worksheet.write(x,7,line['saldo'] if line['saldo'] else '0.00',formats['numberdos'])
			worksheet.write(x,8,line['moneda'] if line['moneda'] else '',formats['especial1'])
			worksheet.write(x,9,line['tc'] if line['tc'] else '0.0000',formats['numbercuatro'])
			worksheet.write(x,10,line['debe_me'] if line['debe_me'] else '0.00',formats['numberdos'])
			worksheet.write(x,11,line['haber_me'] if line['haber_me'] else '0.00',formats['numberdos'])
			worksheet.write(x,12,line['saldo_me'] if line['saldo_me'] else '0.00',formats['numberdos'])
			worksheet.write(x,13,line['cta_analitica'] if line['cta_analitica'] else '',formats['especial1'])
			worksheet.write(x,14,line['glosa'] if line['glosa'] else '',formats['especial1'])
			worksheet.write(x,15,line['td_partner'] if line['td_partner'] else '',formats['especial1'])
			worksheet.write(x,16,line['doc_partner'] if line['doc_partner'] else '',formats['especial1'])
			worksheet.write(x,17,line['partner'] if line['partner'] else '',formats['especial1'])
			worksheet.write(x,18,line['td_sunat'] if line['td_sunat'] else '',formats['especial1'])
			worksheet.write(x,19,line['nro_comprobante'] if line['nro_comprobante'] else '',formats['especial1'])
			worksheet.write(x,20,line['fecha_doc'] if line['fecha_doc'] else '',formats['dateformat'])
			worksheet.write(x,21,line['fecha_ven'] if line['fecha_ven'] else '',formats['dateformat'])
			x += 1

		widths = [10,9,7,11,8,10,10,12,5,7,11,11,11,17,47,4,11,40,3,16,12,12]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()

		f = open(direccion +'LibroCajaBancos.xlsx', 'rb')
		return self.env['popup.it'].get_file('LibroCajaBancos.xlsx',base64.encodebytes(b''.join(f.readlines())))
	
	def get_header(self):
		HEADERS = ['PERIODO','FECHA','LIBRO','VOUCHER','CUENTA','DEBE','HABER','SALDO MN','MON','TC','DEBE ME', 'HABER ME', 'SALDO ME',
		'CTA ANALITICA','GLOSA','TDP','RUC','PARTNER','TD','NRO COMP','FECHA DOC','FECHA VEN']
		return HEADERS

	def domain_dates(self):
		if self.date_from:
			if self.fiscal_year_id.date_from.year != self.date_from.year:
				raise UserError("La fecha inicial no esta en el rango del Año Fiscal escogido (Ejercicio).")
		if self.date_to:
			if self.fiscal_year_id.date_from.year != self.date_to.year:
				raise UserError("La fecha final no esta en el rango del Año Fiscal escogido (Ejercicio).")
		if self.date_from and self.date_to:
			if self.date_to < self.date_from:
				raise UserError("La fecha final no puede ser menor a la fecha inicial.")