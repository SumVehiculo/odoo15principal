# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError
import base64

class WorksheetF1Wizard(models.TransientModel):
	_name = 'worksheet.f1.wizard'

	name = fields.Char()
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	fiscal_year_id = fields.Many2one('account.fiscal.year',string='Ejercicio',required=True)
	period_from = fields.Many2one('account.period',string='Periodo Inicial',required=True)
	period_to = fields.Many2one('account.period',string='Periodo Final',required=True)
	type_show =  fields.Selection([('pantalla','Pantalla'),('excel','Excel')],default='excel',string=u'Mostrar en', required=True)
	level = fields.Selection([('balance','Balance'),('register','Registro')],default='balance',string='Nivel',required=True)
	show_header = fields.Boolean(string='Mostrar cabecera',default=False)
	show_closed = fields.Boolean(string='Mostrar con Cierre',default=False)

	@api.onchange('company_id')
	def get_fiscal_year(self):
		if self.company_id:
			today = fields.Date.context_today(self)
			fiscal_year = self.env['account.fiscal.year'].search([('name','=',str(today.year))],limit=1)
			if fiscal_year:
				self.fiscal_year_id = fiscal_year.id

	def _get_f1_register_sql(self):
		sql = """
			select '{date_from}'::date as date_from,
			'{date_to}'::date as date_to, T.* from (
			(select 
			left(a2.code,2) as mayor,
			a2.code as cuenta,
			a2.name as nomenclatura,
			a1.debe,
			a1.haber,
			case when a1.debe > a1.haber then a1.debe-a1.haber else  0 end as saldo_deudor,
			case when a1.haber> a1.debe then a1.haber-a1.debe else 0 end as saldo_acreedor,
			case when a2.clasification_sheet='0' and a1.debe>a1.haber then a1.debe-a1.haber else 0 end as activo,
			case when a2.clasification_sheet='0' and a1.haber>a1.debe then a1.haber-a1.debe else 0 end as pasivo,
			case when (a2.clasification_sheet='1' or a2.clasification_sheet='3') and a1.debe>a1.haber then a1.debe-a1.haber else 0 end as perdinat,
			case when (a2.clasification_sheet='1' or a2.clasification_sheet='3') and a1.haber>a1.debe then a1.haber-a1.debe else 0 end as ganannat,
			case when (a2.clasification_sheet='2' or a2.clasification_sheet='3') and a1.debe>a1.haber then a1.debe-a1.haber else 0 end as perdifun,
			case when (a2.clasification_sheet='2' or a2.clasification_sheet='3') and a1.haber>a1.debe then a1.haber-a1.debe else 0 end as gananfun
			from get_sumas_mayor_f1('{date_from}','{date_to}',{company_id},{show_closed}) a1
			left join account_account a2 on a2.id=a1.account_id
			order by a2.code)
			UNION ALL
			(select
			null::character varying as mayor,
			null::character varying as cuenta,
			'SUMAS'::character varying as nomenclatura,
			sum(a1.debe) as debe,
			sum(a1.haber) as haber,
			sum(case when a1.debe > a1.haber then a1.debe-a1.haber else  0 end) as saldo_deudor,
			sum(case when a1.haber> a1.debe then a1.haber-a1.debe else 0 end) as saldo_acreedor,
			sum(case when a2.clasification_sheet='0' and a1.debe>a1.haber then a1.debe-a1.haber else 0 end) as activo,
			sum(case when a2.clasification_sheet='0' and a1.haber>a1.debe then a1.haber-a1.debe else 0 end) as pasivo,
			sum(case when (a2.clasification_sheet='1' or a2.clasification_sheet='3') and a1.debe>a1.haber then a1.debe-a1.haber else 0 end) as perdinat,
			sum(case when (a2.clasification_sheet='1' or a2.clasification_sheet='3') and a1.haber>a1.debe then a1.haber-a1.debe else 0 end) as ganannat,
			sum(case when (a2.clasification_sheet='2' or a2.clasification_sheet='3') and a1.debe>a1.haber then a1.debe-a1.haber else 0 end) as perdifun,
			sum(case when (a2.clasification_sheet='2' or a2.clasification_sheet='3') and a1.haber>a1.debe then a1.haber-a1.debe else 0 end) as gananfun
			from get_sumas_mayor_f1('{date_from}','{date_to}',{company_id},{show_closed}) a1
			left join account_account a2 on a2.id=a1.account_id)
			UNION ALL
			(
				SELECT 
				null::character varying as mayor,
				null::character varying as cuenta,
				'UTILIDAD O PERDIDA'::character varying as nomenclatura,
				case
					when sum(a1.debe) < sum(a1.haber)
					then sum(a1.haber) - sum(a1.debe)
					else 0
				end as debe,
				case
					when sum(a1.debe) > sum(a1.haber)
					then sum(a1.debe) - sum(a1.haber) 
					else 0
				end as haber,
				case
					when sum(case when a1.debe > a1.haber then a1.debe-a1.haber else  0 end) < sum(case when a1.haber> a1.debe then a1.haber-a1.debe else 0 end)
					then sum(case when a1.haber> a1.debe then a1.haber-a1.debe else 0 end) - sum(case when a1.debe > a1.haber then a1.debe-a1.haber else  0 end)
					else 0
				end as saldo_deudor,
				case
					when sum(case when a1.debe > a1.haber then a1.debe-a1.haber else  0 end) > sum(case when a1.haber> a1.debe then a1.haber-a1.debe else 0 end)
					then sum(case when a1.debe > a1.haber then a1.debe-a1.haber else  0 end) - sum(case when a1.haber> a1.debe then a1.haber-a1.debe else 0 end)
					else 0
				end as saldo_acreedor,
				case
					when sum(case when a2.clasification_sheet='0' and a1.debe>a1.haber then a1.debe-a1.haber else 0 end) < sum(case when a2.clasification_sheet='0' and a1.haber>a1.debe then a1.haber-a1.debe else 0 end)
					then sum(case when a2.clasification_sheet='0' and a1.haber>a1.debe then a1.haber-a1.debe else 0 end) - sum(case when a2.clasification_sheet='0' and a1.debe>a1.haber then a1.debe-a1.haber else 0 end)
					else 0
				end as activo,
				case
					when sum(case when a2.clasification_sheet='0' and a1.debe>a1.haber then a1.debe-a1.haber else 0 end) > sum(case when a2.clasification_sheet='0' and a1.haber>a1.debe then a1.haber-a1.debe else 0 end)
					then sum(case when a2.clasification_sheet='0' and a1.debe>a1.haber then a1.debe-a1.haber else 0 end) - sum(case when a2.clasification_sheet='0' and a1.haber>a1.debe then a1.haber-a1.debe else 0 end)
					else 0
				end as pasivo,
				case
					when sum(case when (a2.clasification_sheet='1' or a2.clasification_sheet='3') and a1.debe>a1.haber then a1.debe-a1.haber else 0 end) < sum(case when (a2.clasification_sheet='1' or a2.clasification_sheet='3') and a1.haber>a1.debe then a1.haber-a1.debe else 0 end)
					then sum(case when (a2.clasification_sheet='1' or a2.clasification_sheet='3') and a1.haber>a1.debe then a1.haber-a1.debe else 0 end) - sum(case when (a2.clasification_sheet='1' or a2.clasification_sheet='3') and a1.debe>a1.haber then a1.debe-a1.haber else 0 end)
					else 0
				end as perdinat,
				case
					when sum(case when (a2.clasification_sheet='1' or a2.clasification_sheet='3') and a1.debe>a1.haber then a1.debe-a1.haber else 0 end) > sum(case when (a2.clasification_sheet='1' or a2.clasification_sheet='3') and a1.haber>a1.debe then a1.haber-a1.debe else 0 end)
					then sum(case when (a2.clasification_sheet='1' or a2.clasification_sheet='3') and a1.debe>a1.haber then a1.debe-a1.haber else 0 end) - sum(case when (a2.clasification_sheet='1' or a2.clasification_sheet='3') and a1.haber>a1.debe then a1.haber-a1.debe else 0 end)
					else 0
				end as ganannat,
				case
					when sum(case when (a2.clasification_sheet='2' or a2.clasification_sheet='3') and a1.debe>a1.haber then a1.debe-a1.haber else 0 end) < sum(case when (a2.clasification_sheet='2' or a2.clasification_sheet='3') and a1.haber>a1.debe then a1.haber-a1.debe else 0 end)
					then sum(case when (a2.clasification_sheet='2' or a2.clasification_sheet='3') and a1.haber>a1.debe then a1.haber-a1.debe else 0 end) - sum(case when (a2.clasification_sheet='2' or a2.clasification_sheet='3') and a1.debe>a1.haber then a1.debe-a1.haber else 0 end)
					else 0
				end as perdifun,
				case
					when sum(case when (a2.clasification_sheet='2' or a2.clasification_sheet='3') and a1.debe>a1.haber then a1.debe-a1.haber else 0 end) > sum(case when (a2.clasification_sheet='2' or a2.clasification_sheet='3') and a1.haber>a1.debe then a1.haber-a1.debe else 0 end)
					then sum(case when (a2.clasification_sheet='2' or a2.clasification_sheet='3') and a1.debe>a1.haber then a1.debe-a1.haber else 0 end) - sum(case when (a2.clasification_sheet='2' or a2.clasification_sheet='3') and a1.haber>a1.debe then a1.haber-a1.debe else 0 end)
					else 0
				end as gananfun
				from get_sumas_mayor_f1('{date_from}','{date_to}',{company_id},{show_closed}) a1
				left join account_account a2 on a2.id=a1.account_id
			)
			)T
		""".format(
				date_from = self.period_from.date_start.strftime('%Y/%m/%d'),
				date_to = self.period_to.date_end.strftime('%Y/%m/%d'),
				company_id = self.company_id.id,
				show_closed = "TRUE" if self.show_closed else "FALSE"
			)
		return sql

	def _get_f1_balance_sql(self):
		sql = """
			select 
			'{date_from}'::date as date_from,
			'{date_to}'::date as date_to, T.* FROM (
			(select
			a2.code_prefix_start as cuenta,
			a2.name as nomenclatura,
			a1.debe,
			a1.haber,
			case when a1.debe > a1.haber then a1.debe-a1.haber else  0 end as saldo_deudor,
			case when a1.haber> a1.debe then a1.haber-a1.debe else 0 end as saldo_acreedor,
			case when a2.clasification_sheet='0' and a1.debe>a1.haber then a1.debe-a1.haber else 0 end as activo,
			case when a2.clasification_sheet='0' and a1.haber>a1.debe then a1.haber-a1.debe else 0 end as pasivo,
			case when (a2.clasification_sheet='1' or a2.clasification_sheet='3') and a1.debe>a1.haber then a1.debe-a1.haber else 0 end as perdinat,
			case when (a2.clasification_sheet='1' or a2.clasification_sheet='3') and a1.haber>a1.debe then a1.haber-a1.debe else 0 end as ganannat,
			case when (a2.clasification_sheet='2' or a2.clasification_sheet='3') and a1.debe>a1.haber then a1.debe-a1.haber else 0 end as perdifun,
			case when (a2.clasification_sheet='2' or a2.clasification_sheet='3') and a1.haber>a1.debe then a1.haber-a1.debe else 0 end as gananfun
			from get_sumas_balance_f1('{date_from}','{date_to}',{company_id},{show_closed}) a1
			left join account_group a2 on a2.id=a1.account_id
			order by a2.code_prefix_start)
			UNION ALL
			(SELECT 
			null::character varying as cuenta,
			'SUMAS'::character varying as nomenclatura,
			sum(a1.debe) as debe,
			sum(a1.haber) as haber,
			sum(case when a1.debe > a1.haber then a1.debe-a1.haber else  0 end) as saldo_deudor,
			sum(case when a1.haber> a1.debe then a1.haber-a1.debe else 0 end) as saldo_acreedor,
			sum(case when a2.clasification_sheet='0' and a1.debe>a1.haber then a1.debe-a1.haber else 0 end) as activo,
			sum(case when a2.clasification_sheet='0' and a1.haber>a1.debe then a1.haber-a1.debe else 0 end) as pasivo,
			sum(case when (a2.clasification_sheet='1' or a2.clasification_sheet='3') and a1.debe>a1.haber then a1.debe-a1.haber else 0 end) as perdinat,
			sum(case when (a2.clasification_sheet='1' or a2.clasification_sheet='3') and a1.haber>a1.debe then a1.haber-a1.debe else 0 end) as ganannat,
			sum(case when (a2.clasification_sheet='2' or a2.clasification_sheet='3') and a1.debe>a1.haber then a1.debe-a1.haber else 0 end) as perdifun,
			sum(case when (a2.clasification_sheet='2' or a2.clasification_sheet='3') and a1.haber>a1.debe then a1.haber-a1.debe else 0 end) as gananfun
			from get_sumas_balance_f1('{date_from}','{date_to}',{company_id},{show_closed}) a1
			left join account_group a2 on a2.id=a1.account_id
			)
			UNION ALL
			(
			SELECT 
			null::character varying as cuenta,
			'UTILIDAD O PERDIDA'::character varying as nomenclatura,
			case
				when sum(a1.debe) < sum(a1.haber)
				then sum(a1.haber) - sum(a1.debe)
				else 0
			end as debe,
			case
				when sum(a1.debe) > sum(a1.haber)
				then sum(a1.debe) - sum(a1.haber) 
				else 0
			end as haber,
			case
				when sum(case when a1.debe > a1.haber then a1.debe-a1.haber else  0 end) < sum(case when a1.haber> a1.debe then a1.haber-a1.debe else 0 end)
				then sum(case when a1.haber> a1.debe then a1.haber-a1.debe else 0 end) - sum(case when a1.debe > a1.haber then a1.debe-a1.haber else  0 end)
				else 0
			end as saldo_deudor,
			case
				when sum(case when a1.debe > a1.haber then a1.debe-a1.haber else  0 end) > sum(case when a1.haber> a1.debe then a1.haber-a1.debe else 0 end)
				then sum(case when a1.debe > a1.haber then a1.debe-a1.haber else  0 end) - sum(case when a1.haber> a1.debe then a1.haber-a1.debe else 0 end)
				else 0
			end as saldo_acreedor,
			case
				when sum(case when a2.clasification_sheet='0' and a1.debe>a1.haber then a1.debe-a1.haber else 0 end) < sum(case when a2.clasification_sheet='0' and a1.haber>a1.debe then a1.haber-a1.debe else 0 end)
				then sum(case when a2.clasification_sheet='0' and a1.haber>a1.debe then a1.haber-a1.debe else 0 end) - sum(case when a2.clasification_sheet='0' and a1.debe>a1.haber then a1.debe-a1.haber else 0 end)
				else 0
			end as activo,
			case
				when sum(case when a2.clasification_sheet='0' and a1.debe>a1.haber then a1.debe-a1.haber else 0 end) > sum(case when a2.clasification_sheet='0' and a1.haber>a1.debe then a1.haber-a1.debe else 0 end)
				then sum(case when a2.clasification_sheet='0' and a1.debe>a1.haber then a1.debe-a1.haber else 0 end) - sum(case when a2.clasification_sheet='0' and a1.haber>a1.debe then a1.haber-a1.debe else 0 end)
				else 0
			end as pasivo,
			case
				when sum(case when (a2.clasification_sheet='1' or a2.clasification_sheet='3') and a1.debe>a1.haber then a1.debe-a1.haber else 0 end) < sum(case when (a2.clasification_sheet='1' or a2.clasification_sheet='3') and a1.haber>a1.debe then a1.haber-a1.debe else 0 end)
				then sum(case when (a2.clasification_sheet='1' or a2.clasification_sheet='3') and a1.haber>a1.debe then a1.haber-a1.debe else 0 end) - sum(case when (a2.clasification_sheet='1' or a2.clasification_sheet='3') and a1.debe>a1.haber then a1.debe-a1.haber else 0 end)
				else 0
			end as perdinat,
			case
				when sum(case when (a2.clasification_sheet='1' or a2.clasification_sheet='3') and a1.debe>a1.haber then a1.debe-a1.haber else 0 end) > sum(case when (a2.clasification_sheet='1' or a2.clasification_sheet='3') and a1.haber>a1.debe then a1.haber-a1.debe else 0 end)
				then sum(case when (a2.clasification_sheet='1' or a2.clasification_sheet='3') and a1.debe>a1.haber then a1.debe-a1.haber else 0 end) - sum(case when (a2.clasification_sheet='1' or a2.clasification_sheet='3') and a1.haber>a1.debe then a1.haber-a1.debe else 0 end)
				else 0
			end as ganannat,
			case
				when sum(case when (a2.clasification_sheet='2' or a2.clasification_sheet='3') and a1.debe>a1.haber then a1.debe-a1.haber else 0 end) < sum(case when (a2.clasification_sheet='2' or a2.clasification_sheet='3') and a1.haber>a1.debe then a1.haber-a1.debe else 0 end)
				then sum(case when (a2.clasification_sheet='2' or a2.clasification_sheet='3') and a1.haber>a1.debe then a1.haber-a1.debe else 0 end) - sum(case when (a2.clasification_sheet='2' or a2.clasification_sheet='3') and a1.debe>a1.haber then a1.debe-a1.haber else 0 end)
				else 0
			end as perdifun,
			case
				when sum(case when (a2.clasification_sheet='2' or a2.clasification_sheet='3') and a1.debe>a1.haber then a1.debe-a1.haber else 0 end) > sum(case when (a2.clasification_sheet='2' or a2.clasification_sheet='3') and a1.haber>a1.debe then a1.haber-a1.debe else 0 end)
				then sum(case when (a2.clasification_sheet='2' or a2.clasification_sheet='3') and a1.debe>a1.haber then a1.debe-a1.haber else 0 end) - sum(case when (a2.clasification_sheet='2' or a2.clasification_sheet='3') and a1.haber>a1.debe then a1.haber-a1.debe else 0 end)
				else 0
			end as gananfun
			from get_sumas_balance_f1('{date_from}','{date_to}',{company_id},{show_closed}) a1
			left join account_group a2 on a2.id=a1.account_id
			)
			)T
		""".format(
				date_from = self.period_from.date_start.strftime('%Y/%m/%d'),
				date_to = self.period_to.date_end.strftime('%Y/%m/%d'),
				company_id = self.company_id.id,
				show_closed = "TRUE" if self.show_closed else "FALSE"
			)
		return sql

	def get_report(self):
		if self.type_show == 'pantalla':
			if self.level == 'register':
				self._cr.execute("""
				DROP VIEW IF EXISTS f1_register;
				CREATE OR REPLACE VIEW f1_register AS 
				(SELECT row_number() OVER () AS id, T.* FROM (%s) T)
				"""%(self._get_f1_register_sql()))
				return self.get_window_f1_register()
			else:
				self._cr.execute("""
				DROP VIEW IF EXISTS f1_balance;
				CREATE OR REPLACE VIEW f1_balance AS 
				(SELECT row_number() OVER () AS id, T.* FROM (%s) T)
				"""%(self._get_f1_balance_sql()))
				return self.get_window_f1_balance()
		else:
			return self.get_excel_f1_register() if self.level == 'register' else self.get_excel_f1_balance()
	
	def get_window_f1_register(self):
		view = self.env.ref('account_htf1_report.view_f1_register_tree').id
		return {
			'name': 'Hoja de Trabajo F1 - Registro',
			'type': 'ir.actions.act_window',
			'res_model': 'f1.register',
			'view_mode': 'tree',
			'views': [(view, 'tree')],
		}

	def get_window_f1_balance(self):
		view = self.env.ref('account_htf1_report.view_f1_balance_tree').id
		return {
			'name': 'Hoja de Trabajo F1 - Balance',
			'type': 'ir.actions.act_window',
			'res_model': 'f1.balance',
			'view_mode': 'tree',
			'views': [(view, 'tree')],
		}

	def get_excel_f1_register(self):
		import io
		from xlsxwriter.workbook import Workbook
		from xlsxwriter.utility import xl_rowcol_to_cell
		ReportBase = self.env['report.base']
		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'Hoja_Trabajo_F1.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		worksheet = workbook.add_worksheet("Hoja de Trabajo F1")
		worksheet.set_tab_color('blue')

		x=0
		if self.show_header:
			worksheet.merge_range(x,0,x,13, u"HOJA DE TRABAJO F1 - REGISTRO", formats['especial5'] )
			x+=2
			worksheet.write(x,0,u"Compañía:",formats['especial2'])
			worksheet.merge_range(x,1,x,13,self.company_id.name,formats['especial2'])
			x+=1
			worksheet.write(x,0,"Periodo Inicial:",formats['especial2'])
			worksheet.merge_range(x,1,x,2,str(self.period_from.code),formats['especial2'])
			x+=1
			worksheet.write(x,0,"Periodo Final:",formats['especial2'])
			worksheet.merge_range(x,1,x,2,str(self.period_to.code),formats['especial2'])
			x+=2

		HEADERS = ['MAYOR','CUENTA','NOMENCLATURA','DEBE','HABER','SALDO DEUDOR','SALDO ACREEDOR',
				   'ACTIVO','PASIVO','PERDINAT','GANANNAT','PERDIFUN','GANANFUN']
		worksheet = ReportBase.get_headers(worksheet,HEADERS,x,0,formats['boldbord'])
		x+=1

		self.env.cr.execute(self._get_f1_register_sql())
		res = self.env.cr.dictfetchall()
		total = len(res)-2

		for c,line in enumerate(res):
			worksheet.write(x,0,line['mayor'] if line['mayor'] else '',formats['especial1'])
			worksheet.write(x,1,line['cuenta'] if line['cuenta'] else '',formats['especial1'])
			worksheet.write(x,2,line['nomenclatura'] if line['nomenclatura'] else '',formats['especial1'] if c < total else formats['boldbord'])
			worksheet.write(x,3,line['debe'] if line['debe'] else 0,formats['numberdos'] if c < total else formats['numbertotal'] )
			worksheet.write(x,4,line['haber'] if line['haber'] else 0,formats['numberdos'] if c < total else formats['numbertotal'] )
			worksheet.write(x,5,line['saldo_deudor'] if line['saldo_deudor'] else 0,formats['numberdos'] if c < total else formats['numbertotal'] )
			worksheet.write(x,6,line['saldo_acreedor'] if line['saldo_acreedor'] else 0,formats['numberdos'] if c < total else formats['numbertotal'] )
			worksheet.write(x,7,line['activo'] if line['activo'] else 0,formats['numberdos'] if c < total else formats['numbertotal'] )
			worksheet.write(x,8,line['pasivo'] if line['pasivo'] else 0,formats['numberdos'] if c < total else formats['numbertotal'] )
			worksheet.write(x,9,line['perdinat'] if line['perdinat'] else 0,formats['numberdos'] if c < total else formats['numbertotal'] )
			worksheet.write(x,10,line['ganannat'] if line['ganannat'] else 0,formats['numberdos'] if c < total else formats['numbertotal'] )
			worksheet.write(x,11,line['perdifun'] if line['perdifun'] else 0,formats['numberdos'] if c < total else formats['numbertotal'] )
			worksheet.write(x,12,line['gananfun'] if line['gananfun'] else 0,formats['numberdos'] if c < total else formats['numbertotal'] )
			x += 1
	
		widths = [10,9,40,10,10,10,10,10,10,10,10,10,10]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()
		f = open(direccion +'Hoja_Trabajo_F1.xlsx', 'rb')
		return self.env['popup.it'].get_file('Hoja Trabajo F1 - Registro.xlsx',base64.encodebytes(b''.join(f.readlines())))

	def get_excel_f1_balance(self):
		import io
		from xlsxwriter.workbook import Workbook
		from xlsxwriter.utility import xl_rowcol_to_cell
		ReportBase = self.env['report.base']
		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'Hoja_Trabajo_F1.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		worksheet = workbook.add_worksheet("Hoja de Trabajo F1")
		worksheet.set_tab_color('blue')

		x=0
		if self.show_header:
			worksheet.merge_range(x,0,x,13, u"HOJA DE TRABAJO F1 - BALANCE", formats['especial5'] )
			x+=2
			worksheet.write(x,0,u"Compañía:",formats['especial2'])
			worksheet.merge_range(x,1,x,13,self.company_id.name,formats['especial2'])
			x+=1
			worksheet.write(x,0,"Periodo Inicial:",formats['especial2'])
			worksheet.merge_range(x,1,x,2,str(self.period_from.code),formats['especial2'])
			x+=1
			worksheet.write(x,0,"Periodo Final:",formats['especial2'])
			worksheet.merge_range(x,1,x,2,str(self.period_to.code),formats['especial2'])
			x+=2

		HEADERS = ['CUENTA','NOMENCLATURA','DEBE','HABER','SALDO DEUDOR','SALDO ACREEDOR',
				   'ACTIVO','PASIVO','PERDINAT','GANANNAT','PERDIFUN','GANANFUN']
		worksheet = ReportBase.get_headers(worksheet,HEADERS,x,0,formats['boldbord'])
		x+=1

		self.env.cr.execute(self._get_f1_balance_sql())
		res = self.env.cr.dictfetchall()
		total = len(res)-2

		for c,line in enumerate(res):
			worksheet.write(x,0,line['cuenta'] if line['cuenta'] else '',formats['especial1'])
			worksheet.write(x,1,line['nomenclatura'] if line['nomenclatura'] else '',formats['especial1'] if c < total else formats['boldbord'])
			worksheet.write(x,2,line['debe'] if line['debe'] else 0,formats['numberdos'] if c < total else formats['numbertotal'] )
			worksheet.write(x,3,line['haber'] if line['haber'] else 0,formats['numberdos'] if c < total else formats['numbertotal'] )
			worksheet.write(x,4,line['saldo_deudor'] if line['saldo_deudor'] else 0,formats['numberdos'] if c < total else formats['numbertotal'] )
			worksheet.write(x,5,line['saldo_acreedor'] if line['saldo_acreedor'] else 0,formats['numberdos'] if c < total else formats['numbertotal'] )
			worksheet.write(x,6,line['activo'] if line['activo'] else 0,formats['numberdos'] if c < total else formats['numbertotal'] )
			worksheet.write(x,7,line['pasivo'] if line['pasivo'] else 0,formats['numberdos'] if c < total else formats['numbertotal'] )
			worksheet.write(x,8,line['perdinat'] if line['perdinat'] else 0,formats['numberdos'] if c < total else formats['numbertotal'] )
			worksheet.write(x,9,line['ganannat'] if line['ganannat'] else 0,formats['numberdos'] if c < total else formats['numbertotal'] )
			worksheet.write(x,10,line['perdifun'] if line['perdifun'] else 0,formats['numberdos'] if c < total else formats['numbertotal'] )
			worksheet.write(x,11,line['gananfun'] if line['gananfun'] else 0,formats['numberdos'] if c < total else formats['numbertotal'] )
			x += 1
		widths = [10,40,10,10,10,10,10,10,10,10,10,10]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()
		f = open(direccion +'Hoja_Trabajo_F1.xlsx', 'rb')
		return self.env['popup.it'].get_file('Hoja Trabajo F1 - Balance.xlsx',base64.encodebytes(b''.join(f.readlines())))