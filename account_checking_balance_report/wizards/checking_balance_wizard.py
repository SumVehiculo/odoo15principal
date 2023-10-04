# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError
import base64

class CheckingBalanceWizard(models.TransientModel):
	_name = 'checking.balance.wizard'

	name = fields.Char()
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	fiscal_year_id = fields.Many2one('account.fiscal.year',string='Ejercicio',required=True)
	period_from = fields.Many2one('account.period',string='Periodo Inicial',required=True)
	period_to = fields.Many2one('account.period',string='Periodo Final',required=True)
	type_show =  fields.Selection([('pantalla','Pantalla'),('excel','Excel')],default='excel',string=u'Mostrar en', required=True)
	show_account_entries = fields.Boolean(string='Mostrar Rubros de Cuenta',default=True)
	level = fields.Selection([('balance','Balance'),('register','Registro')],default='balance',string='Nivel',required=True)
	show_header = fields.Boolean(string='Mostrar cabecera',default=False)

	@api.onchange('company_id')
	def get_fiscal_year(self):
		if self.company_id:
			today = fields.Date.context_today(self)
			fiscal_year = self.env['account.fiscal.year'].search([('name','=',str(today.year))],limit=1)
			if fiscal_year:
				self.fiscal_year_id = fiscal_year.id

	def _get_register_sql(self):
		sql = """select 
			left(a2.code,2) as mayor,
			a2.code as cuenta,
			a2.name as nomenclatura,
			a1.debe,
			a1.haber,
			case when a1.debe > a1.haber then a1.debe-a1.haber else  0 end as saldo_deudor,
			case when a1.haber> a1.debe then a1.haber-a1.debe else 0 end as saldo_acreedor,
			ati.name as rubro
			from get_sumas_mayor_f1('{date_from}','{date_to}',{company_id},TRUE) a1
			left join account_account a2 on a2.id=a1.account_id
			left join account_type_it ati on ati.id = a2.account_type_it_id
			order by a2.code
		""".format(
				date_from = self.period_from.date_start.strftime('%Y/%m/%d'),
				date_to = self.period_to.date_end.strftime('%Y/%m/%d'),
				company_id = self.company_id.id
			)
		return sql
	
	def _get_balance_sql(self):
		sql = """select 
			a2.code_prefix_start as cuenta,
			a2.name as nomenclatura,
			a1.debe,
			a1.haber,
			case when a1.debe > a1.haber then a1.debe-a1.haber else  0 end as saldo_deudor,
			case when a1.haber> a1.debe then a1.haber-a1.debe else 0 end as saldo_acreedor
			from get_sumas_balance_f1('{date_from}','{date_to}',{company_id},TRUE) a1
			left join account_group a2 on a2.id=a1.account_id
			order by a2.code_prefix_start
		""".format(
				date_from = self.period_from.date_start.strftime('%Y/%m/%d'),
				date_to = self.period_to.date_end.strftime('%Y/%m/%d'),
				company_id = self.company_id.id
			)
		return sql

	def get_report(self):
		if self.type_show == 'pantalla':
			if self.level == 'register':
				self._cr.execute("""
				CREATE OR REPLACE VIEW checking_register AS 
				(SELECT row_number() OVER () AS id, T.* FROM (%s) T)
				"""%(self._get_register_sql()))
				return self.get_window_checking_register()
			else:
				self._cr.execute("""
				CREATE OR REPLACE VIEW checking_balance AS 
				(SELECT row_number() OVER () AS id, T.* FROM (%s) T)
				"""%(self._get_balance_sql()))
				return self.get_window_checking_balance()
		else:
			return self.get_excel_checking_register() if self.level == 'register' else self.get_excel_checking_balance()
	
	def get_window_checking_register(self):
		if self.show_account_entries:
			view = self.env.ref('account_checking_balance_report.view_checking_register_tree_true').id
		else:
			view = self.env.ref('account_checking_balance_report.view_checking_register_tree').id
		return {
			'type': 'ir.actions.act_window',
			'res_model': 'checking.register',
			'view_mode': 'tree',
			'views': [(view, 'tree')],
		}

	def get_window_checking_balance(self):
		view = self.env.ref('account_checking_balance_report.view_checking_balance_tree').id
		return {
			'type': 'ir.actions.act_window',
			'res_model': 'checking.balance',
			'view_mode': 'tree',
			'views': [(view, 'tree')],
		}

	def get_excel_checking_register(self):
		import io
		from xlsxwriter.workbook import Workbook
		from xlsxwriter.utility import xl_rowcol_to_cell
		ReportBase = self.env['report.base']
		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'Balance_Comprobacion.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		worksheet = workbook.add_worksheet("Balance Comprobacion")
		worksheet.set_tab_color('blue')

		x=0
		if self.show_header:
			worksheet.merge_range(x,0,x,10, u"BALANCE DE COMPROBACIÓN - REGISTRO", formats['especial5'] )
			x+=2
			worksheet.write(x,0,u"Compañía:",formats['especial2'])
			worksheet.merge_range(x,1,x,10,self.company_id.name,formats['especial2'])
			x+=1
			worksheet.write(x,0,"Periodo Inicial:",formats['especial2'])
			worksheet.merge_range(x,1,x,2,str(self.period_from.code),formats['especial2'])
			x+=1
			worksheet.write(x,0,"Periodo Final:",formats['especial2'])
			worksheet.merge_range(x,1,x,2,str(self.period_to.code),formats['especial2'])
			x+=2

		HEADERS = ['MAYOR','CUENTA','NOMENCLATURA','DEBE','HABER','SALDO DEUDOR','SALDO ACREEDOR']
		if self.show_account_entries:
			HEADERS.append('RUBRO ESTADO FINANCIERO')
		worksheet = ReportBase.get_headers(worksheet,HEADERS,x,0,formats['boldbord'])
		x+=1
		c=1

		self.env.cr.execute(self._get_register_sql())
		res = self.env.cr.dictfetchall()

		for line in res:
			worksheet.write(x,0,line['mayor'] if line['mayor'] else '',formats['especial1'])
			worksheet.write(x,1,line['cuenta'] if line['cuenta'] else '',formats['especial1'])
			worksheet.write(x,2,line['nomenclatura'] if line['nomenclatura'] else '',formats['especial1'])
			worksheet.write(x,3,line['debe'] if line['debe'] else 0,formats['numberdos'] )
			worksheet.write(x,4,line['haber'] if line['haber'] else 0,formats['numberdos'] )
			worksheet.write(x,5,line['saldo_deudor'] if line['saldo_deudor'] else 0,formats['numberdos'] )
			worksheet.write(x,6,line['saldo_acreedor'] if line['saldo_acreedor'] else 0,formats['numberdos'] )
			if self.show_account_entries:
				worksheet.write(x,7,line['rubro'] if line['rubro'] else '',formats['especial1'])
			x += 1
		if c != x:
			x += 1
			worksheet.write_formula(x,3, '=sum(' + xl_rowcol_to_cell(c,3) +':' +xl_rowcol_to_cell(x-1,3) + ')', formats['numbertotal'])
			worksheet.write_formula(x,4, '=sum(' + xl_rowcol_to_cell(c,4) +':' +xl_rowcol_to_cell(x-1,4) + ')', formats['numbertotal'])
			worksheet.write_formula(x,5, '=sum(' + xl_rowcol_to_cell(c,5) +':' +xl_rowcol_to_cell(x-1,5) + ')', formats['numbertotal'])
			worksheet.write_formula(x,6, '=sum(' + xl_rowcol_to_cell(c,6) +':' +xl_rowcol_to_cell(x-1,6) + ')', formats['numbertotal'])

		widths = [10,9,40,10,10,12,12]
		if self.show_account_entries:
			widths.append(33)
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()
		f = open(direccion +'Balance_Comprobacion.xlsx', 'rb')
		return self.env['popup.it'].get_file(u'Balance Comprobación - Registro.xlsx',base64.encodebytes(b''.join(f.readlines())))

	def get_excel_checking_balance(self):
		import io
		from xlsxwriter.workbook import Workbook
		from xlsxwriter.utility import xl_rowcol_to_cell
		ReportBase = self.env['report.base']
		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'Balance_Comprobacion.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		worksheet = workbook.add_worksheet("Balance Comprobacion")
		worksheet.set_tab_color('blue')

		x=0
		if self.show_header:
			worksheet.merge_range(x,0,x,6, u"BALANCE DE COMPROBACIÓN - BALANCE", formats['especial5'] )
			x+=2
			worksheet.write(x,0,u"Compañía:",formats['especial2'])
			worksheet.merge_range(x,1,x,6,self.company_id.name,formats['especial2'])
			x+=1
			worksheet.write(x,0,"Periodo Inicial:",formats['especial2'])
			worksheet.merge_range(x,1,x,2,str(self.period_from.code),formats['especial2'])
			x+=1
			worksheet.write(x,0,"Periodo Final:",formats['especial2'])
			worksheet.merge_range(x,1,x,2,str(self.period_to.code),formats['especial2'])
			x+=2

		HEADERS = ['MAYOR','NOMENCLATURA','DEBE','HABER','SALDO DEUDOR','SALDO ACREEDOR']
		worksheet = ReportBase.get_headers(worksheet,HEADERS,x,0,formats['boldbord'])
		x+=1
		c=1

		self.env.cr.execute(self._get_balance_sql())
		res = self.env.cr.dictfetchall()

		for line in res:
			worksheet.write(x,0,line['cuenta'] if line['cuenta'] else '',formats['especial1'])
			worksheet.write(x,1,line['nomenclatura'] if line['nomenclatura'] else '',formats['especial1'])
			worksheet.write(x,2,line['debe'] if line['debe'] else 0,formats['numberdos'] )
			worksheet.write(x,3,line['haber'] if line['haber'] else 0,formats['numberdos'] )
			worksheet.write(x,4,line['saldo_deudor'] if line['saldo_deudor'] else 0,formats['numberdos'] )
			worksheet.write(x,5,line['saldo_acreedor'] if line['saldo_acreedor'] else 0,formats['numberdos'] )
			x += 1
		if c != x:
			x += 1
			worksheet.write_formula(x,2, '=sum(' + xl_rowcol_to_cell(c,2) +':' +xl_rowcol_to_cell(x-1,2) + ')', formats['numbertotal'])
			worksheet.write_formula(x,3, '=sum(' + xl_rowcol_to_cell(c,3) +':' +xl_rowcol_to_cell(x-1,3) + ')', formats['numbertotal'])
			worksheet.write_formula(x,4, '=sum(' + xl_rowcol_to_cell(c,4) +':' +xl_rowcol_to_cell(x-1,4) + ')', formats['numbertotal'])
			worksheet.write_formula(x,5, '=sum(' + xl_rowcol_to_cell(c,5) +':' +xl_rowcol_to_cell(x-1,5) + ')', formats['numbertotal'])

		widths = [10,40,10,10,12,12]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()
		f = open(direccion +'Balance_Comprobacion.xlsx', 'rb')
		return self.env['popup.it'].get_file(u'Balance Comprobación - Balance.xlsx',base64.encodebytes(b''.join(f.readlines())))