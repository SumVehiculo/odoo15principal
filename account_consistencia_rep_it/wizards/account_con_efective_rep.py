# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError
import base64

class AccountConEfectiveRep(models.TransientModel):
	_name = 'account.con.efective.rep'
	_description = 'Account Con Efective Rep'

	name = fields.Char()
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	fiscal_year_id = fields.Many2one('account.fiscal.year',string=u'Ejercicio',required=True)
	period_from = fields.Many2one('account.period',string='Periodo Inicial',required=True)
	period_to = fields.Many2one('account.period',string='Periodo Final',required=True)
	type_show =  fields.Selection([('pantalla','Pantalla'),('excel','Excel')],string=u'Mostrar en', required=True, default='pantalla')

	@api.onchange('company_id')
	def get_fiscal_year(self):
		if self.company_id:
			today = fields.Date.context_today(self)
			fiscal_year = self.env['account.fiscal.year'].search([('name','=',str(today.year))],limit=1)
			if fiscal_year:
				self.fiscal_year_id = fiscal_year.id

	def get_report(self):

		sql = """
			CREATE OR REPLACE view account_con_efective_book as ("""+self._get_sql()+""")"""

		self.env.cr.execute(sql)

		if self.type_show == 'pantalla':
			return {
				'name': 'Consistencia Flujo Efectivo',
				'type': 'ir.actions.act_window',
				'res_model': 'account.con.efective.book',
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

		workbook = Workbook(direccion +'Const_Flujo_Efectivo.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		##########CONSISTENCIA FLUJO EFECTIVO############
		worksheet = workbook.add_worksheet("CONSISTENCIA FLUJO EFECTIVO")
		worksheet.set_tab_color('blue')

		HEADERS = ['CUENTA','T FLUJO EFECTIVO','INGRESO','EGRESO','BALANCE']
		worksheet = ReportBase.get_headers(worksheet,HEADERS,0,0,formats['boldbord'])
		x=1

		ingreso,egreso,balance = 0,0,0

		for line in self.env['account.con.efective.book'].search([]):
			worksheet.write(x,0,line.account_code if line.account_code else '',formats['especial1'])
			worksheet.write(x,1,line.account_efective_type_name if line.account_efective_type_name else '',formats['especial1'])
			worksheet.write(x,2,line.ingreso if line.ingreso else '0.00',formats['numberdos'])
			worksheet.write(x,3,line.egreso if line.egreso else '0.00',formats['numberdos'])
			worksheet.write(x,4,line.balance if line.balance else '0.00',formats['numberdos'])
			ingreso += line.ingreso if line.ingreso else 0
			egreso += line.egreso if line.egreso else 0
			balance += line.balance if line.balance else 0

			x += 1

		#TOTALES

		worksheet.write(x,2,ingreso,formats['numbertotal'])
		worksheet.write(x,3,egreso,formats['numbertotal'])
		worksheet.write(x,4,balance,formats['numbertotal'])

		widths = [9,56,12,12,12]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()

		f = open(direccion +'Const_Flujo_Efectivo.xlsx', 'rb')
		return self.env['popup.it'].get_file('Consistencia Flujo Efectivo.xlsx',base64.encodebytes(b''.join(f.readlines())))

	def _get_sql(self):
		sql = """
				SELECT row_number() OVER () AS id,
				T.account_code,
				T.account_efective_type_name,
				T.ingreso,
				T.egreso,
				T.balance
				FROM
				(SELECT
				vst_d.cuenta AS account_code,
				ati.name AS account_efective_type_name,
				sum(vst_d.haber) as ingreso,
				sum(vst_d.debe) as egreso, 
				sum(haber-debe) as balance 
				FROM get_diariog('{date_from}','{date_to}',{company_id}) vst_d 
				LEFT JOIN account_account aa ON aa.id = vst_d.account_id
				LEFT JOIN account_efective_type ati ON ati.id = aa.account_type_cash_id
				WHERE vst_d.move_id IN(
				SELECT move_id FROM get_diariog('{date_from}','{date_to}',{company_id})
				WHERE LEFT(cuenta,2)='10' AND RIGHT(periodo::character varying,2) NOT IN ('00','13') )
				AND LEFT(vst_d.cuenta,2)<>'10'
				GROUP BY vst_d.cuenta,ati.name) T
			""".format(
				date_from = self.period_from.date_start.strftime('%Y/%m/%d'),
				date_to = self.period_to.date_end.strftime('%Y/%m/%d'),
				company_id = self.company_id.id
			)

		return sql