# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError
import base64

class AccountDesSummaryRep(models.TransientModel):
	_name = 'account.des.summary.rep'

	name = fields.Char()
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	fiscal_year_id = fields.Many2one('account.fiscal.year',string=u'Ejercicio',required=True)
	period = fields.Many2one('account.period',string='Periodo',required=True)
	type_show =  fields.Selection([('pantalla','Pantalla'),('excel','Excel')],string=u'Mostrar en', required=True, default='pantalla')

	def get_report(self):
		sql = """
			DROP VIEW IF EXISTS account_des_summary_book;
			CREATE OR REPLACE view account_des_summary_book as (SELECT row_number() OVER () AS id,a1.* FROM get_summary_destinos(%s,%d) a1)""" % (
				self.period.code,self.company_id.id)

		self.env.cr.execute(sql)

		if self.type_show == 'pantalla':
			return {
				'name': 'Resumen Destinos',
				'type': 'ir.actions.act_window',
				'res_model': 'account.des.summary.book',
				'view_mode': 'tree',
				'view_type': 'form',
				'views': [(False, 'tree')],
			}

		if self.type_show == 'excel':
			return self.get_excel()

	def get_excel(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']
		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'Resumen_Destino.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		##########RESUMEN DESTINO############
		worksheet = workbook.add_worksheet("RESUMEN DESTINO")
		worksheet.set_tab_color('blue')

		HEADERS = ['CUENTA','BALANCE','CTA 20','CTA 24','CTA 25','CTA 26','CTA 90','CTA 91','CTA 92','CTA 93','CTA 94','CTA 95','CTA 96','CTA 97','CTA 98','CTA 99']
		worksheet = ReportBase.get_headers(worksheet,HEADERS,0,0,formats['boldbord'])
		x=1

		for line in self.env['account.des.summary.book'].search([]):
			worksheet.write(x,0,line.cuenta if line.cuenta else '',formats['especial1'])
			worksheet.write(x,1,line.balance if line.balance else '0.00',formats['numberdos'])
			worksheet.write(x,2,line.cta20 if line.cta20 else '0.00',formats['numberdos'])
			worksheet.write(x,3,line.cta24 if line.cta24 else '0.00',formats['numberdos'])
			worksheet.write(x,4,line.cta25 if line.cta25 else '0.00',formats['numberdos'])
			worksheet.write(x,5,line.cta26 if line.cta26 else '0.00',formats['numberdos'])
			worksheet.write(x,6,line.cta90 if line.cta90 else '0.00',formats['numberdos'])
			worksheet.write(x,7,line.cta91 if line.cta91 else '0.00',formats['numberdos'])
			worksheet.write(x,8,line.cta92 if line.cta92 else '0.00',formats['numberdos'])
			worksheet.write(x,9,line.cta93 if line.cta93 else '0.00',formats['numberdos'])
			worksheet.write(x,10,line.cta94 if line.cta94 else '0.00',formats['numberdos'])
			worksheet.write(x,11,line.cta95 if line.cta95 else '0.00',formats['numberdos'])
			worksheet.write(x,12,line.cta96 if line.cta96 else '0.00',formats['numberdos'])
			worksheet.write(x,13,line.cta97 if line.cta97 else '0.00',formats['numberdos'])
			worksheet.write(x,14,line.cta98 if line.cta98 else '0.00',formats['numberdos'])
			worksheet.write(x,15,line.cta99 if line.cta99 else '0.00',formats['numberdos'])
			x += 1

		widths = [8,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()

		f = open(direccion +'Resumen_Destino.xlsx', 'rb')
		return self.env['popup.it'].get_file('Resumen Destino.xlsx',base64.encodebytes(b''.join(f.readlines())))