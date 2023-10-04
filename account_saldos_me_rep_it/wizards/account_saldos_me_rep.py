# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import date
from odoo.exceptions import UserError
import base64

class AccountSaldosMeRep(models.TransientModel):
	_name = 'account.saldos.me.rep'

	name = fields.Char()
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	fiscal_year_id = fields.Many2one('account.fiscal.year',string='Ejercicio',required=True)
	period_from = fields.Many2one('account.period',string='Periodo Inicial',required=True)
	period_to = fields.Many2one('account.period',string='Periodo Final',required=True)
	type_show = fields.Selection([('pantalla','Pantalla'),('excel','Excel')],string=u'Mostrar en',default='pantalla', required=True)

	@api.onchange('company_id')
	def get_fiscal_year(self):
		if self.company_id:
			today = fields.Date.context_today(self)
			fiscal_year = self.env['account.fiscal.year'].search([('name','=',str(today.year))],limit=1)
			if fiscal_year:
				self.fiscal_year_id = fiscal_year.id

	def _get_sql(self):
		sql = """SELECT row_number() OVER () AS id, T.* FROM (select * from get_saldos_me_rep('%s','%s',%d))T
		""" % (self.period_from.code,
			self.period_to.code,
			self.company_id.id)
		return sql

	def get_report(self):
		self.env.cr.execute("""
			CREATE OR REPLACE view account_saldos_me_book as ("""+self._get_sql()+""")""")
			
		if self.type_show == 'pantalla':
			return {
				'name': 'Saldos Moneda Extranjera',
				'type': 'ir.actions.act_window',
				'res_model': 'account.saldos.me.book',
				'view_mode': 'tree',
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

		workbook = Workbook(direccion +'Saldos_me.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		##########Saldos Moneda Extranjera############
		worksheet = workbook.add_worksheet("Saldos Moneda Extranjera")
		worksheet.set_tab_color('blue')

		HEADERS = ['CUENTA','DENOMINACION','MONEDA','DEBE MN','HABER MN','SALDO MN','DEBE ME','HABER ME','SALDO ME']
		worksheet = ReportBase.get_headers(worksheet,HEADERS,0,0,formats['boldbord'])
		x=1

		for line in self.env['account.saldos.me.book'].search([]):
			worksheet.write(x,0,line.cuenta if line.cuenta else '',formats['especial1'])
			worksheet.write(x,1,line.denominacion if line.denominacion else '',formats['especial1'])
			worksheet.write(x,2,line.moneda if line.moneda else '',formats['especial1'])
			worksheet.write(x,3,line.debe if line.debe else '0.00',formats['numberdos'])
			worksheet.write(x,4,line.haber if line.haber else '0.00',formats['numberdos'])
			worksheet.write(x,5,line.saldo if line.saldo else '0.00',formats['numberdos'])
			worksheet.write(x,6,line.debe_me if line.debe_me else '0.00',formats['numberdos'])
			worksheet.write(x,7,line.haber_me if line.haber_me else '0.00',formats['numberdos'])
			worksheet.write(x,8,line.saldo_me if line.saldo_me else '0.00',formats['numberdos'])
			x += 1

		widths = [12,25,12,15,15,15,15,15,15]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()

		f = open(direccion +'Saldos_me.xlsx', 'rb')
		return self.env['popup.it'].get_file('Saldos Moneda Extranjera.xlsx',base64.encodebytes(b''.join(f.readlines())))