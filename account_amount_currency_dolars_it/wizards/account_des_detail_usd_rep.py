# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError
import base64

class AccountDesDetailUsdRep(models.TransientModel):
	_name = 'account.des.detail.usd.rep'

	name = fields.Char()
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	exercise = fields.Many2one('account.fiscal.year',string=u'Ejercicio',required=True)
	period = fields.Many2one('account.period',string='Periodo',required=True)
	type_show =  fields.Selection([('pantalla','Pantalla'),('excel','Excel')],string=u'Mostrar en', required=True, default='pantalla')

	@api.onchange('company_id')
	def get_fiscal_year(self):
		if self.company_id:
			fiscal_year = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).fiscal_year
			if fiscal_year:
				self.exercise = fiscal_year.id

	def get_report(self):

		sql = """
			CREATE OR REPLACE view account_des_detail_usd_book as (SELECT row_number() OVER () AS id,T.* FROM 
			(select a1.*, left(a1.cuenta,2) as mayorf, left(a1.des_debe,2) as mayord, 
			CASE
				WHEN a2.amount_c > 0::numeric THEN a2.amount_c
				ELSE 0::numeric
			END AS debe_me,
			CASE
				WHEN a2.amount_c < 0::numeric THEN abs(a2.amount_c)
				ELSE 0::numeric
			END AS haber_me,
			a2.amount_c as balance_me
			from get_destinos('%s',%s) a1
			left join account_move_line a2 on a2.id=a1.aml_id) T)""" % (
				str(self.period.code),
				str(self.company_id.id)
			)

		self.env.cr.execute(sql)

		if self.type_show == 'pantalla':
			return {
				'name': 'Detalle Destinos',
				'type': 'ir.actions.act_window',
				'res_model': 'account.des.detail.usd.book',
				'view_mode': 'tree,pivot,graph',
				'view_type': 'form',
			}

		if self.type_show == 'excel':
			return self.get_excel()

	def get_excel(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']
		direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'Detalle_Destino.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		##########DETALLE DESTINO############
		worksheet = workbook.add_worksheet("DETALLE DESTINO")
		worksheet.set_tab_color('blue')

		HEADERS = ['PERIODO','FECHA','LIBRO','VOUCHER','MAYOR F','MAYOR D','CUENTA','DEBE','HABER','BALANCE','DEBE ME','HABER ME','BALANCE ME',
		'CTA ANALITICA','DEST DEBE','DEST HABER']
		worksheet = ReportBase.get_headers(worksheet,HEADERS,0,0,formats['boldbord'])
		x=1

		for line in self.env['account.des.detail.usd.book'].search([]):
			worksheet.write(x,0,line.periodo if line.periodo else '',formats['especial1'])
			worksheet.write(x,1,line.fecha if line.fecha else '',formats['dateformat'])
			worksheet.write(x,2,line.libro if line.libro else '',formats['especial1'])
			worksheet.write(x,3,line.voucher if line.voucher else '',formats['especial1'])
			worksheet.write(x,4,line.mayorf if line.mayorf else '',formats['especial1'])
			worksheet.write(x,5,line.mayord if line.mayord else '',formats['especial1'])
			worksheet.write(x,6,line.cuenta if line.cuenta else '',formats['especial1'])
			worksheet.write(x,7,line.debe if line.debe else '0.00',formats['numberdos'])
			worksheet.write(x,8,line.haber if line.haber else '0.00',formats['numberdos'])
			worksheet.write(x,9,line.balance if line.balance else '0.00',formats['numberdos'])
			worksheet.write(x,10,line.debe_me if line.debe_me else '0.00',formats['numberdos'])
			worksheet.write(x,11,line.haber_me if line.haber_me else '0.00',formats['numberdos'])
			worksheet.write(x,12,line.balance_me if line.balance_me else '0.00',formats['numberdos'])
			worksheet.write(x,13,line.cta_analitica if line.cta_analitica else '',formats['especial1'])
			worksheet.write(x,14,line.des_debe if line.des_debe else '',formats['especial1'])
			worksheet.write(x,15,line.des_haber if line.des_haber else '',formats['especial1'])
			x += 1

		widths = [9,9,7,11,10,10,8,10,10,10,12,12,12,13,12,12]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()

		f = open(direccion +'Detalle_Destino.xlsx', 'rb')
		return self.env['popup.it'].get_file('Detalle Destino USD.xlsx',base64.encodestring(b''.join(f.readlines())))