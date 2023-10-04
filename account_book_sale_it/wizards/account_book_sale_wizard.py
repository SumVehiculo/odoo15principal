
# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError
import base64

from io import BytesIO
import re
import uuid

class AccountBookSaleWizard(models.TransientModel):
	_name = 'account.book.sale.wizard'
	_description = 'Account Book Sale Wizard'

	name = fields.Char()
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	fiscal_year_id = fields.Many2one('account.fiscal.year',string=u'Ejercicio',required=True)
	date_from = fields.Date(string=u'Fecha Inicial')
	date_to = fields.Date(string=u'Fecha Final')
	period_from_id = fields.Many2one('account.period',string='Periodo Inicial')
	period_to_id = fields.Many2one('account.period',string='Periodo Final')
	show_by = fields.Selection([('date','Fechas'),('period','Periodos')],string='Mostrar en base a',default='date')
	type_show =  fields.Selection([('pantalla','Pantalla'),('excel','Excel'),('csv','CSV')],string=u'Mostrar en',default='pantalla')
	currency = fields.Selection([('pen','PEN'),('usd','USD')],string=u'Moneda',default='pen', required=True)
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
		
		if self.type_show == 'pantalla':
			self.env.cr.execute("""
			DROP VIEW IF EXISTS account_book_sale_view CASCADE;
			CREATE OR REPLACE view account_book_sale_view as (SELECT row_number() OVER () AS id, T.* FROM ("""+self._get_sql()+""")T)""")
			if self.currency == 'pen':
				view_id = self.env.ref('account_book_sale_it.view_account_book_sale_view_tree')
			else:
				view_id = self.env.ref('account_book_sale_it.view_account_book_sale_usd_view_tree')
			return {
				'name': 'Registro de Ventas',
				'type': 'ir.actions.act_window',
				'res_model': 'account.book.sale.view',
				'view_mode': 'tree',
				'view_type': 'form',
				'view_id': view_id.id,
			}
		if self.type_show == 'excel':
			return self.get_excel()
		
		if self.type_show == 'csv':
			return self.getCsv()

	def get_excel(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']

		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'Registro_Ventas.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		##########REGISTRO VENTAS############
		worksheet = workbook.add_worksheet("REGISTRO VENTAS")
		worksheet.set_tab_color('blue')
		x=0
		if self.show_header:
			worksheet.merge_range(x,0,x,12, "REGISTRO DE VENTAS", formats['especial5'] )
			x+=2
			worksheet.write(x,0,u"Compañía:",formats['especial2'])
			worksheet.merge_range(x,1,x,12,self.company_id.name,formats['especial2'])
			x+=1
			worksheet.write(x,0,"Fecha Inicial:",formats['especial2'])
			worksheet.merge_range(x,1,x,2,str(self.date_from.strftime('%Y/%m/%d') if self.show_by == 'date' else self.period_from_id.date_start.strftime('%Y/%m/%d')),formats['especial2'])
			x+=1
			worksheet.write(x,0,"Fecha Final:",formats['especial2'])
			worksheet.merge_range(x,1,x,2,str(self.date_to.strftime('%Y/%m/%d') if self.show_by == 'date' else self.period_to_id.date_end.strftime('%Y/%m/%d')),formats['especial2'])
			x+=2
		worksheet = ReportBase.get_headers(worksheet,self.get_header(),x,0,formats['boldbord'])
		self.env.cr.execute(self._get_sql())
		res = self.env.cr.dictfetchall()
		c = 1 if self.currency=='pen' else 0
		x+=1

		#DECLARANDO TOTALES
		exp, venta_g, inaf, exo, isc_v, otros_v, icbper, igv_v, total = 0, 0, 0, 0, 0, 0, 0, 0, 0

		for line in res:
			worksheet.write(x,0,line['periodo'] if line['periodo'] else '',formats['especial1'])
			worksheet.write(x,1,line['fecha_cont'] if line['fecha_cont'] else '',formats['dateformat'])
			worksheet.write(x,2,line['libro'] if line['libro'] else '',formats['especial1'])
			worksheet.write(x,3,line['voucher'] if line['voucher'] else '',formats['especial1'])
			worksheet.write(x,4,line['fecha_e'] if line['fecha_e'] else '',formats['dateformat'])
			worksheet.write(x,5,line['fecha_v'] if line['fecha_v'] else '',formats['dateformat'])
			worksheet.write(x,6,line['td'] if line['td'] else '',formats['especial1'])
			worksheet.write(x,7,line['serie'] if line['serie'] else '',formats['especial1'])
			worksheet.write(x,8,line['anio'] if line['anio'] else '',formats['especial1'])
			worksheet.write(x,9,line['numero'] if line['numero'] else '',formats['especial1'])
			worksheet.write(x,10,line['tdp'] if line['tdp'] else '',formats['especial1'])
			worksheet.write(x,11,line['docp'] if line['docp'] else '',formats['especial1'])
			worksheet.write(x,12,line['namep'] if line['namep'] else '',formats['especial1'])
			worksheet.write(x,13,line['exp'] if line['exp'] else '0.00',formats['numberdos'])
			worksheet.write(x,14,line['venta_g'] if line['venta_g'] else '0.00',formats['numberdos'])
			worksheet.write(x,15,line['inaf'] if line['inaf'] else '0.00',formats['numberdos'])
			worksheet.write(x,16,line['exo'] if line['exo'] else '0.00',formats['numberdos'])
			worksheet.write(x,17,line['isc_v'] if line['isc_v'] else '0.00',formats['numberdos'])
			worksheet.write(x,18,line['icbper'] if line['icbper'] else '0.00',formats['numberdos'])
			worksheet.write(x,19,line['otros_v'] if line['otros_v'] else '0.00',formats['numberdos'])
			worksheet.write(x,20,line['igv_v'] if line['igv_v'] else '0.00',formats['numberdos'])
			worksheet.write(x,21,line['total'] if line['total'] else '0.00',formats['numberdos'])
			worksheet.write(x,22,line['name'] if line['name'] else '',formats['especial1'])
			if self.currency=='pen':
				worksheet.write(x,23,line['monto_me'] if line['monto_me'] else '0.00',formats['numberdos'])
			worksheet.write(x,c+23,line['currency_rate'] if line['currency_rate'] else '0.0000',formats['numbercuatro'])
			worksheet.write(x,c+24,line['fecha_det'] if line['fecha_det'] else '',formats['dateformat'])
			worksheet.write(x,c+25,line['comp_det'] if line['comp_det'] else '',formats['especial1'])
			worksheet.write(x,c+26,line['f_doc_m'] if line['f_doc_m'] else '',formats['dateformat'])
			worksheet.write(x,c+27,line['td_doc_m'] if line['td_doc_m'] else '',formats['especial1'])
			worksheet.write(x,c+28,line['serie_m'] if line['serie_m'] else '',formats['especial1'])
			worksheet.write(x,c+29,line['numero_m'] if line['numero_m'] else '',formats['especial1'])
			worksheet.write(x,c+30,line['glosa'] if line['glosa'] else '',formats['especial1'])
			x += 1

			exp += line['exp'] if line['exp'] else 0
			venta_g += line['venta_g'] if line['venta_g'] else 0
			inaf += line['inaf'] if line['inaf'] else 0
			exo += line['exo'] if line['exo'] else 0
			isc_v += line['isc_v'] if line['isc_v'] else 0
			otros_v += line['otros_v'] if line['otros_v'] else 0
			icbper += line['icbper'] if line['icbper'] else 0
			igv_v += line['igv_v'] if line['igv_v'] else 0
			total += line['total'] if line['total'] else 0

		worksheet.write(x,13,exp,formats['numbertotal'])
		worksheet.write(x,14,venta_g,formats['numbertotal'])
		worksheet.write(x,15,inaf,formats['numbertotal'])
		worksheet.write(x,16,exo,formats['numbertotal'])
		worksheet.write(x,17,isc_v,formats['numbertotal'])
		worksheet.write(x,18,icbper,formats['numbertotal'])
		worksheet.write(x,19,otros_v,formats['numbertotal'])
		worksheet.write(x,20,igv_v,formats['numbertotal'])
		worksheet.write(x,21,total,formats['numbertotal'])

		if self.currency=='pen':
			widths = [11,12,7,11,10,10,3,10,10,10,4,12,40,10,10,10,10,10,10,10,10,12,5,12,7,12,12,12,12,12,12,60]
		else:
			widths = [11,12,7,11,10,10,3,10,10,10,4,12,40,10,10,10,10,10,10,10,10,12,5,7,12,12,12,12,12,12,60]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()

		f = open(direccion +'Registro_Ventas.xlsx', 'rb')
		return self.env['popup.it'].get_file('RV%s.xlsx'%(self.company_id.partner_id.vat),base64.encodebytes(b''.join(f.readlines())))

	def getCsv(self):
		ReportBase = self.env['report.base']
		workbook = ReportBase.get_file_sql_export(self._get_sql(),',',True)
		return self.env['popup.it'].get_file('RV%s.csv'%(self.company_id.partner_id.vat),workbook)

	def get_header(self):
		if self.currency == 'pen':
			HEADERS = ['PERIODO','FECHA CONT','LIBRO','VOUCHER','FECHA EM','FECHA VEN','TD','SERIE',u'AÑO',u'NÚMERO','TDP','RUC','PARTNER',
			'EXP','VENTA G','INAF','EXO','ISC V','ICBPER','OTROS V','IGV','TOTAL','MON','MONTO ME','TC','FECHA DET','COMP DET',
			'FECHA DOC M','TD DOC M','SERIE M','NUMERO M','GLOSA']
		else:
			HEADERS = ['PERIODO','FECHA CONT','LIBRO','VOUCHER','FECHA EM','FECHA VEN','TD','SERIE',u'AÑO',u'NÚMERO','TDP','RUC','PARTNER',
			'EXP','VENTA G','INAF','EXO','ISC V','ICBPER','OTROS V','IGV','TOTAL','MON','TC','FECHA DET','COMP DET',
			'FECHA DOC M','TD DOC M','SERIE M','NUMERO M','GLOSA']
		return HEADERS


	def _get_sql(self):
		if self.currency == 'pen':
			sql = """SELECT periodo::character varying, fecha_cont, libro, voucher, fecha_e, fecha_v, td, 
					serie, anio, numero, tdp, docp, namep, exp, venta_g, inaf, exo, isc_v, icbper,
					otros_v, igv_v, total, name, monto_me, currency_rate, fecha_det, 
					comp_det, f_doc_m, td_doc_m, serie_m, numero_m, glosa
					from get_ventas_1_1('%s','%s',%d,'%s')
				""" % (self.date_from.strftime('%Y/%m/%d') if self.show_by == 'date' else self.period_from_id.date_start.strftime('%Y/%m/%d'),
					self.date_to.strftime('%Y/%m/%d') if self.show_by == 'date' else self.period_to_id.date_end.strftime('%Y/%m/%d'),
					self.company_id.id,
					self.currency)
		else:
			sql = """SELECT periodo::character varying, fecha_cont, libro, voucher, fecha_e, fecha_v, td, 
					serie, anio, numero, tdp, docp, namep, exp, venta_g, inaf, exo, isc_v, icbper,
					otros_v, igv_v, total, name, 0 as monto_me, currency_rate, fecha_det, 
					comp_det, f_doc_m, td_doc_m, serie_m, numero_m, glosa
					from get_ventas_1_1('%s','%s',%d,'%s')
				""" % (self.date_from.strftime('%Y/%m/%d') if self.show_by == 'date' else self.period_from_id.date_start.strftime('%Y/%m/%d'),
					self.date_to.strftime('%Y/%m/%d') if self.show_by == 'date' else self.period_to_id.date_end.strftime('%Y/%m/%d'),
					self.company_id.id,
					self.currency)
		return sql

	def domain_dates(self):
		if self.show_by == 'date':
			if self.date_from:
				if self.fiscal_year_id.date_from.year != self.date_from.year:
					raise UserError("La fecha inicial no esta en el rango del Año Fiscal escogido (Ejercicio).")
			if self.date_to:
				if self.fiscal_year_id.date_from.year != self.date_to.year:
					raise UserError("La fecha final no esta en el rango del Año Fiscal escogido (Ejercicio).")
			if self.date_from and self.date_to:
				if self.date_to < self.date_from:
					raise UserError("La fecha final no puede ser menor a la fecha inicial.")