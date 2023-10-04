# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError
import base64

class AccountDesDetailRep(models.TransientModel):
	_name = 'account.des.detail.rep'

	name = fields.Char()
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	fiscal_year_id = fields.Many2one('account.fiscal.year',string=u'Ejercicio',required=True)
	period_from = fields.Many2one('account.period',string='Periodo Inicial',required=True)
	period_to = fields.Many2one('account.period',string='Periodo Final',required=True)
	type_show =  fields.Selection([('pantalla','Pantalla'),('excel','Excel')],string=u'Mostrar en', required=True, default='pantalla')

	def get_report(self):

		sql = """
			DROP VIEW IF EXISTS account_des_detail_book;
			CREATE OR REPLACE view account_des_detail_book as (SELECT row_number() OVER () AS id,a1.* FROM get_destinos(%s,%s,%d) a1)""" % (
				self.period_from.code,self.period_to.code,self.company_id.id)

		self.env.cr.execute(sql)

		if self.type_show == 'pantalla':
			return {
				'name': 'Detalle Destinos',
				'type': 'ir.actions.act_window',
				'res_model': 'account.des.detail.book',
				'view_mode': 'tree,pivot,graph',
				'view_type': 'form',
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

		workbook = Workbook(direccion +'Detalle_Destino.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		##########DETALLE DESTINO############
		worksheet = workbook.add_worksheet("DETALLE DESTINO")
		worksheet.set_tab_color('blue')

		HEADERS = ['PERIODO','FECHA','LIBRO','VOUCHER','CUENTA','DEBE','HABER','BALANCE',
		'CTA ANALITICA','DEST DEBE','DEST HABER']
		worksheet = ReportBase.get_headers(worksheet,HEADERS,0,0,formats['boldbord'])
		x=1

		for line in self.env['account.des.detail.book'].search([]):
			worksheet.write(x,0,str(line.periodo) if line.periodo else '',formats['especial1'])
			worksheet.write(x,1,line.fecha if line.fecha else '',formats['dateformat'])
			worksheet.write(x,2,line.libro if line.libro else '',formats['especial1'])
			worksheet.write(x,3,line.voucher if line.voucher else '',formats['especial1'])
			worksheet.write(x,4,line.cuenta if line.cuenta else '',formats['especial1'])
			worksheet.write(x,5,line.debe if line.debe else '0.00',formats['numberdos'])
			worksheet.write(x,6,line.haber if line.haber else '0.00',formats['numberdos'])
			worksheet.write(x,7,line.balance if line.balance else '0.00',formats['numberdos'])
			worksheet.write(x,8,line.cta_analitica if line.cta_analitica else '',formats['especial1'])
			worksheet.write(x,9,line.des_debe if line.des_debe else '',formats['especial1'])
			worksheet.write(x,10,line.des_haber if line.des_haber else '',formats['especial1'])
			x += 1

		widths = [9,9,7,11,8,10,10,10,13,12,12]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()

		f = open(direccion +'Detalle_Destino.xlsx', 'rb')
		return self.env['popup.it'].get_file('Detalle Destino.xlsx',base64.encodebytes(b''.join(f.readlines())))