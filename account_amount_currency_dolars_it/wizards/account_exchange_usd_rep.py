# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError
import base64

class AccountExchangeUsdRep(models.TransientModel):
	_name = 'account.exchange.usd.rep'

	name = fields.Char()
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	fiscal_year_id = fields.Many2one('account.fiscal.year',string=u'Ejercicio',required=True)
	period = fields.Many2one('account.period',string=u'Periodo',required=True)
	journal_id = fields.Many2one('account.journal',string=u'Diario')
	type_show =  fields.Selection([('pantalla','Pantalla'),('excel','Excel')],string=u'Mostrar en',default='pantalla')

	@api.onchange('company_id')
	def get_fiscal_year(self):
		if self.company_id:
			fiscal_year = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).fiscal_year
			if fiscal_year:
				self.fiscal_year_id = fiscal_year.id
			else:
				raise UserError(u'No existe un año Fiscal configurado en Parametros Principales de Contabilidad para esta Compañía')

	def get_report(self):
		self.env.cr.execute("""
			CREATE OR REPLACE view account_exchange_usd_book as ("""+self._get_sql_report(self.fiscal_year_id.name,self.period,self.company_id.id)+""")""")
			
		if self.type_show == 'pantalla':
			return {
				'name': 'Registro Diferencia ME Global',
				'type': 'ir.actions.act_window',
				'res_model': 'account.exchange.usd.book',
				'view_mode': 'tree',
				'view_type': 'form',
				'views': [(False, 'tree')],
			}

		if self.type_show == 'excel':
			return self.get_excel()

	def do_invoice(self):
		if not self.journal_id:
			raise UserError('Falta asignar un diario')
		sql_not_journal = "'{%s}'"%('0')
		param = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1)
		if param.journal_exchange_exclude:
			sql_not_journal = "'{%s}'" % (','.join(str(i) for i in param.journal_exchange_exclude.ids))

		sql = """SELECT account_id, diferencia FROM get_saldos_me_global_final_usd('%s','%s',%d,%s)""" % (self.fiscal_year_id.name,self.period.code,self.company_id.id,sql_not_journal)
		self.env.cr.execute(sql)
		obj =self.env.cr.dictfetchall()
		if len(obj) == 0:
			raise UserError('No existen diferencias de cambio en el periodo %s'%(self.period.name))
		lineas = []
		ganancia = 0
		perdida = 0
		currency = self.env.ref('base.USD')
		for elemnt in obj:
			vals = (0,0,{
				'account_id': elemnt['account_id'],
				'name': 'AJUSTE POR DIFERENCIA DE CAMBIO MENSUAL '+self.period.code,
				'amount_c': elemnt['diferencia'],
				'currency_id': currency.id,
				'company_id': self.company_id.id,
			})
			ganancia+= elemnt['diferencia']*-1 if elemnt['diferencia'] > 0 else 0
			perdida+= elemnt['diferencia']*-1 if elemnt['diferencia'] < 0 else 0
			lineas.append(vals)

		if ganancia != 0:
			profit_account_id = self.env['exchange.diff.config'].search([('company_id','=',self.company_id.id)],limit=1).profit_account_id
			vals_loss = (0,0,{
					'account_id': profit_account_id.id,
					'name': 'AJUSTE POR DIFERENCIA DE CAMBIO MENSUAL '+self.period.code,
					'amount_c': ganancia,
					'company_id': self.company_id.id,
				})
			lineas.append(vals_loss)

		if perdida != 0:
			loss_account_id = self.env['exchange.diff.config'].search([('company_id','=',self.company_id.id)],limit=1).loss_account_id
			vals_profit = (0,0,{
					'account_id': loss_account_id.id,
					'name': 'AJUSTE POR DIFERENCIA DE CAMBIO MENSUAL '+self.period.code,
					'amount_c': perdida,
					'company_id': self.company_id.id,
				})
			lineas.append(vals_profit)
		
		move_id = self.env['account.move'].create({
			'company_id': self.company_id.id,
			'journal_id': self.journal_id.id,
			'date': self.period.date_end,
			'ref': 'DC'+self.period.code+'MN',
			'glosa': 'AJUSTE POR DIFERENCIA DE CAMBIO MENSUAL '+self.period.code,
			'line_ids':lineas})

		if move_id.state == "draft":
			move_id.post()

		return {
			'view_mode': 'form',
			'view_id': self.env.ref('account.view_move_form').id,
			'res_model': 'account.move',
			'type': 'ir.actions.act_window',
			'res_id': move_id.id,
		}

	def get_excel(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']

		direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'Diferencia_ME_Global.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		##########DIFERENCIA ME GLOBAL############
		worksheet = workbook.add_worksheet("DIFERENCIA ME GLOBAL")
		worksheet.set_tab_color('blue')

		HEADERS = ['PERIODO','CUENTA','SALDO ME','SALDO MN','TC','SALDO ACT','DIFERENCIA','CTA DIFERENCIA']
		worksheet = ReportBase.get_headers(worksheet,HEADERS,0,0,formats['boldbord'])
		x=1

		for line in self.env['account.exchange.usd.book'].search([]):
			worksheet.write(x,0,line.periodo if line.periodo else '',formats['especial1'])
			worksheet.write(x,1,line.cuenta if line.cuenta else '',formats['especial1'])
			worksheet.write(x,2,line.saldome if line.saldome else '0.00',formats['numberdos'])
			worksheet.write(x,3,line.saldomn if line.saldomn else '0.00',formats['numberdos'])
			worksheet.write(x,4,line.tc if line.tc else '0.0000',formats['numbercuatro'])
			worksheet.write(x,5,line.saldo_act if line.saldo_act else '0.00',formats['numberdos'])
			worksheet.write(x,6,line.diferencia if line.diferencia else '0.00',formats['numberdos'])
			worksheet.write(x,7,line.cuenta_diferencia if line.cuenta_diferencia else '',formats['especial1'])
			x += 1

		widths = [10,12,15,15,5,15,15,20]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()

		f = open(direccion +'Diferencia_ME_Global.xlsx', 'rb')
		return self.env['popup.it'].get_file('Diferencia ME Global.xlsx',base64.encodestring(b''.join(f.readlines())))

	def _get_sql_report(self,fiscal_year,period,company_id):
		sql_not_journal = "'{%s}'"%('0')
		param = self.env['main.parameter'].search([('company_id','=',company_id)],limit=1)
		if param.journal_exchange_exclude:
			sql_not_journal = "'{%s}'" % (','.join(str(i) for i in param.journal_exchange_exclude.ids))
		sql = """SELECT 
				row_number() OVER () AS id,
				'%s' as periodo,
				aa.code as cuenta,
				gsm.saldomn,
				gsm.saldome,
				gsm.tc,
				gsm.saldo_act,
				gsm.diferencia,
				aa2.code as cuenta_diferencia,
				gsm.account_id,
				%d as period_id
				FROM get_saldos_me_global_final_usd('%s','%s',%d,%s) gsm
				LEFT JOIN account_account aa ON aa.id = gsm.account_id
				LEFT JOIN account_account aa2 ON aa2.id = gsm.difference_account_id
			""" % (period.code,
				period.id,
				fiscal_year,
				period.code,
				company_id,
				sql_not_journal)

		return sql