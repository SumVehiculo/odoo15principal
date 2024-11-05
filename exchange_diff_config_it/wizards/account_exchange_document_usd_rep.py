# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError
import base64

class AccountExchangeDocumentUsdRep(models.TransientModel):
	_name = 'account.exchange.document.usd.rep'

	name = fields.Char()
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)

	def get_fiscal_year(self):
		today = fields.Date.context_today(self)
		fiscal_year = self.env['account.fiscal.year'].search([('name','=',str(today.year))],limit=1)
		if not fiscal_year:
			raise UserError(u'No existe un año fiscal con el año actual.')
		else:
			return fiscal_year.id

	fiscal_year_id = fields.Many2one('account.fiscal.year',string=u'Año Fiscal',default=lambda self:self.get_fiscal_year(),required=True)
	period = fields.Many2one('account.period',string=u'Periodo',required=True)
	type_show =  fields.Selection([('pantalla','Pantalla'),('excel','Excel')],string=u'Mostrar en',default='pantalla')

	def get_report(self):
		self.env.cr.execute("""
			DROP VIEW IF EXISTS account_exchange_document_book CASCADE;
			CREATE OR REPLACE view account_exchange_document_book as ("""+self._get_sql_report(self.fiscal_year_id.name,self.period,self.company_id.id)+""")""")
			
		if self.type_show == 'pantalla':
			return {
				'name': 'Diferencia Documentos Pagados',
				'type': 'ir.actions.act_window',
				'res_model': 'account.exchange.document.book',
				'view_mode': 'tree',
				'view_type': 'form',
				'views': [(False, 'tree')],
			}

		if self.type_show == 'excel':
			return self.get_excel()

	def do_invoice(self):
		dt_perception = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dt_perception
		destination_journal = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).destination_journal

		if not dt_perception:
			raise UserError(u'No existe Tipo de Documento Percepciones configurado en Parametros Generales de Contabilidad para su Compañía.')

		if not destination_journal:
			raise UserError(u'No existe un Diario Asiento Automático configurado en Parametros Generales de Contabilidad para su Compañía.')

		profit_account_id = self.env['exchange.diff.config'].search([('company_id','=',self.company_id.id)],limit=1).profit_account_id
		loss_account_id = self.env['exchange.diff.config'].search([('company_id','=',self.company_id.id)],limit=1).loss_account_id

		sql = """SELECT smd.* FROM get_saldos_me_documento_final('%s','%s',%d) smd
				 WHERE smd.diferencia <> 0 and smd.saldome = 0""" % (self.fiscal_year_id.name,self.period.code,self.company_id.id)
		self.env.cr.execute(sql)
		obj =self.env.cr.fetchall()
		if len(obj) == 0:
			raise UserError('No existen diferencias de cambio en el periodo %s'%(self.period.name))
		lineas = []
		sum_credit = 0
		sum_debit = 0
		pen = self.env.ref('base.PEN')
		for elemnt in obj:
			acc_ob = self.env['account.account'].browse(elemnt[1])
			vals = (0,0,{
				'partner_id': elemnt[0],
				'account_id': elemnt[1],
				'name': 'DIFERENCIA DE CAMBIO '+str('{:02d}'.format(self.period.date_start.month))+'-'+self.fiscal_year_id.name,
				'debit': 0 if elemnt[12] > 0 else abs(elemnt[12]),
				'credit': 0 if elemnt[12] < 0 else abs(elemnt[12]),
				'amount_currency': 0,
				'currency_id': acc_ob.currency_id.id,
				'type_document_id': elemnt[8],
				'nro_comp': elemnt[3],
				'tc':1,
				'company_id': self.company_id.id,
			})
			sum_credit+= 0 if elemnt[12] < 0 else abs(elemnt[12])
			sum_debit+= 0 if elemnt[12] > 0 else abs(elemnt[12])
			lineas.append(vals)

		if sum_credit > 0:
			vals_loss = (0,0,{
					'account_id': loss_account_id.id,
					'name': 'DIFERENCIA DE CAMBIO '+str('{:02d}'.format(self.period.date_start.month))+'-'+self.fiscal_year_id.name,
					'debit': sum_credit,
					'credit': 0,
					'amount_currency': 0,
					'currency_id': pen.id,
					'type_document_id': dt_perception.id,
					'nro_comp': 'dif-'+str('{:02d}'.format(self.period.date_start.month))+'-'+self.fiscal_year_id.name,
					'tc':1,
					'company_id': self.company_id.id,
				})
			lineas.append(vals_loss)

		if sum_debit > 0:
			vals_profit = (0,0,{
					'account_id': profit_account_id.id,
					'name': 'DIFERENCIA DE CAMBIO '+str('{:02d}'.format(self.period.date_start.month))+'-'+self.fiscal_year_id.name,
					'debit': 0,
					'credit': sum_debit,
					'amount_currency': 0,
					'currency_id': pen.id,
					'type_document_id': dt_perception.id,
					'nro_comp': 'dif-'+str('{:02d}'.format(self.period.date_start.month))+'-'+self.fiscal_year_id.name,
					'tc':1,
					'company_id': self.company_id.id,
				})
			lineas.append(vals_profit)
		
		move_id = self.env['account.move'].create({
			'company_id': self.company_id.id,
			'journal_id': destination_journal.id,
			'date': self.period.date_end,
			'ref': 'dif-'+str('{:02d}'.format(self.period.date_start.month))+'-'+self.fiscal_year_id.name,
			'glosa': 'DIFERENCIA DE CAMBIO DE '+str('{:02d}'.format(self.period.date_start.month))+'-'+self.fiscal_year_id.name,
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

		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'Diferencia_ME_Documento.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		##########DIFERENCIA ME DOCUMENTO############
		worksheet = workbook.add_worksheet("DIFERENCIA DOCUMENTOS PAGADOS")
		worksheet.set_tab_color('blue')

		HEADERS = ['PERIODO','CUENTA','PARTNER','TD','NRO COMP.','DEBE','HABER','SALDO MN','SALDO ME','TC','SALDO ACT','DIFERENCIA','CTA DIFERENCIA']
		worksheet = ReportBase.get_headers(worksheet,HEADERS,0,0,formats['boldbord'])
		x=1

		for line in self.env['account.exchange.document.book'].search([]):
			worksheet.write(x,0,line.periodo if line.periodo else '',formats['especial1'])
			worksheet.write(x,1,line.cuenta if line.cuenta else '',formats['especial1'])
			worksheet.write(x,2,line.partner if line.partner else '',formats['especial1'])
			worksheet.write(x,3,line.td_sunat if line.td_sunat else '',formats['especial1'])
			worksheet.write(x,4,line.nro_comprobante if line.nro_comprobante else '',formats['especial1'])
			worksheet.write(x,5,line.debe if line.debe else '0.00',formats['numberdos'])
			worksheet.write(x,6,line.haber if line.haber else '0.00',formats['numberdos'])
			worksheet.write(x,7,line.saldomn if line.saldomn else '0.00',formats['numberdos'])
			worksheet.write(x,8,line.saldome if line.saldome else '0.00',formats['numberdos'])
			worksheet.write(x,9,line.tc if line.tc else '0.0000',formats['numbercuatro'])
			worksheet.write(x,10,line.saldo_act if line.saldo_act else '0.00',formats['numberdos'])
			worksheet.write(x,11,line.diferencia if line.diferencia else '0.00',formats['numberdos'])
			worksheet.write(x,12,line.cuenta_diferencia if line.cuenta_diferencia else '',formats['especial1'])
			x += 1

		widths = [10,12,40,6,15,12,12,15,15,5,15,15,20]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()

		f = open(direccion +'Diferencia_ME_Documento.xlsx', 'rb')
		return self.env['popup.it'].get_file('Diferencia Documentos Pagados.xlsx',base64.encodebytes(b''.join(f.readlines())))

	def _get_sql_report(self,fiscal_year,period,company_id):
		sql_partner_adjustment = ""
		partner_adjustment_id = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).partner_adjustment_id
		
		if partner_adjustment_id:
			sql_partner_adjustment = "AND vst.partner_id <> %d"%(partner_adjustment_id.id)

		sql = """SELECT 
				row_number() OVER () AS id,
				'%s' as periodo,
				aa.code as cuenta,
				rp.name as partner,
				vst.td_sunat,
				vst.nro_comprobante,
				vst.debe,
				vst.haber,
				vst.saldomn,
				vst.saldome,
				vst.tc,
				vst.saldo_act,
				vst.diferencia,
				aa2.code as cuenta_diferencia,
				vst.account_id,
				aa.currency_id,
				vst.partner_id,
				%d as period_id
				FROM get_saldos_me_documento_final('%s','%s',%d) vst
				LEFT JOIN account_account aa ON aa.id = vst.account_id
				LEFT JOIN account_account aa2 ON aa2.id = vst.difference_account_id
				LEFT JOIN res_partner rp ON rp.id = vst.partner_id
				WHERE vst.saldome = 0 
				%s
			""" % (period.code,
				period.id,
				fiscal_year,
				period.code,
				company_id,
				sql_partner_adjustment)

		return sql