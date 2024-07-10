# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError
import base64
from io import BytesIO
import re
import uuid

class AccountSunatBalanceInventoryRep(models.TransientModel):
	_name = 'account.sunat.balance.inventory.rep'
	_description = 'Account Sunat Balance Inventory Rep'

	name = fields.Char()

	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	fiscal_year_id = fields.Many2one('account.fiscal.year',string=u'Ejercicio')
	period = fields.Many2one('account.period',string='Periodo')
	cc = fields.Selection([('01',u'Al 31 de diciembre'),
							('02',u'Al 31 de enero, por modificación del porcentaje'),
							('03',u'Al 30 de junio, por modificación del coeficiente o porcentaje'),
							('04',u'Al último día del mes que sustentará la suspensión o modificación del coeficiente (distinto al 31 de enero o 30 de junio)'),
							('05',u'Al día anterior a la entrada en vigencia de la fusión, escisión y demás formas de reorganización de sociedades o empresas o extinción de la persona jurídica'),
							('06',u'A la fecha del balance de liquidación, cierre o cese definitivo del deudor tributario'),
							('07',u'A la fecha de presentación para libre propósito')],default='01',string=u'Código de oportunidad de presentación del EEFF')
	date = fields.Date(string='Fecha')

	show_all = fields.Boolean(string=u'Mostrar Todo',default=False)

	show_1 = fields.Boolean(string=u'3.1 - ESTADO DE SITUACIÓN FINANCIERA',default=False)
	show_2 = fields.Boolean(string=u'3.2 - CTA. 10 EFECTIVO Y EQUIVALENTES DE EFECTIVO',default=False)
	show_3 = fields.Boolean(string=u'3.3 - CTA. 12 CTA POR COBRAR COM. – TERC. Y 13 CTA POR COBRAR COM. – REL.',default=False)
	show_4 = fields.Boolean(string=u'3.4 - CTA. 14 CTA POR COBRAR AL PERSONAL, ACCIONISTAS, DIRECTORES Y GERENTES',default=False)
	show_5 = fields.Boolean(string=u'3.5 - CTA. 16 CTA POR COBRAR DIV. - TERC. O CTA. 17 CTA POR COBRAR DIV. - REL.',default=False)
	show_6 = fields.Boolean(string=u'3.6 - CTA. 19 ESTIMACIÓN DE CTA DE COBRANZA DUDOSA',default=False)
	show_7 = fields.Boolean(string=u'3.7 - CTA. 20 - MERCADERIAS Y LA CTA. 21 - PROD. TERMINADOS',default=False)
	show_8 = fields.Boolean(string=u'3.8 - CTA. 30 INVERSIONES MOBILIARIAS',default=False)
	show_9 = fields.Boolean(string=u'3.9 - CTA. 34 - INTANGIBLES',default=False)
	show_10 = fields.Boolean(string=u'3.11 - CTA. 41 REMUNERACIONES Y PARTICIPACIONES POR PAGAR',default=False)
	show_11 = fields.Boolean(string=u'3.12 - CTA. 42 CTA POR PAGAR COM. – TERC. Y LA CTA. 43 CTA POR PAGAR COM. – REL.',default=False)
	show_12 = fields.Boolean(string=u'3.13 - CTA. 46 CTA POR PAGAR DIV. – TERC. Y DE LA CTA. 47 CTA POR PAGAR DIV. – REL.',default=False)
	show_13 = fields.Boolean(string=u'3.14 - CTA. 47 - BEN. SOCIALES DE LOS TRABAJADORES (PCGR) - NO APLICA PARA EL PCGE',default=False)
	show_14 = fields.Boolean(string=u'3.15 - CTA. 37 ACTIVO DIFERIDO Y DE LA CTA. 49 PASIVO DIFERIDO',default=False)
	show_15 = fields.Boolean(string=u'3.16.1 - CTA. 50 CAPITAL',default=False)
	show_16 = fields.Boolean(string=u'3.16.2 - EST. DE LA PARTICIPACIÓN ACCIONARIA SOCIALES',default=False)
	show_17 = fields.Boolean(string=u'3.17 - BALANCE DE COMPROBACIÓN',default=False)
	show_18 = fields.Boolean(string=u'3.18 - ESTADO DE FLUJOS DE EFECTIVO - MÉTODO DIRECTO',default=False)
	show_19 = fields.Boolean(string=u'3.19 - ESTADO DE CAMBIOS EN EL PATRIMONIO NETO',default=False)
	show_20 = fields.Boolean(string=u'3.20 - ESTADO DE RESULTADOS',default=False)
	show_21 = fields.Boolean(string=u'3.24 - ESTADO DE RESULTADOS INTEGRALES',default=False)
	show_22 = fields.Boolean(string=u'3.25 - ESTADO DE FLUJOS DE EFECTIVO - MÉTODO INDIRECTO',default=False)

	@api.onchange('show_all')
	def action_add_all(self):
		for i in range(1, 23):
			setattr(self, f'show_{i}', self.show_all)

	@api.onchange('company_id')
	def get_fiscal_year(self):
		if self.company_id:
			today = fields.Date.context_today(self)
			fiscal_year = self.env['account.fiscal.year'].search([('name','=',str(today.year))],limit=1)
			if fiscal_year:
				self.fiscal_year_id = fiscal_year.id
			
	@api.onchange('date')
	def get_period(self):
		if self.date and self.cc in ('05','06','07'):
			self.fiscal_year_id = self.env['account.fiscal.year'].search([('name','=',self.date.strftime('%Y'))],limit=1).id
			self.period = self.env['account.period'].search([('code','=',self.date.strftime('%Y%m')),('fiscal_year_id','=',self.fiscal_year_id.id)],limit=1).id

	def get_balance_inventory(self):
		if not any(getattr(self, f'show_{i}', False) for i in range(1, 23)):
			raise UserError(u'Debe escoger al menos un libro en la Pestaña "Libros"')
		
		kwargs = {}
		for i in range(1, 23):
			show_attr = getattr(self, f'show_{i}')
			kwargs[f'output_name_{i}'], kwargs[f'output_file_{i}'] = self._get_ple(i) if show_attr else (None, None)

		return self.env['popup.it.balance.inventory'].get_file(**kwargs)
	
	def _get_sql_030100(self,period,company_id,cc,date):
		catalog_fs_bi = self.env['account.main.parameter'].search([('company_id','=',company_id)],limit=1).catalog_fs_bi
		if not catalog_fs_bi:
			raise UserError(u'Es necesario configurar el campo "Catálogo de Estados Financieros" en la pestaña "Libros de Inventarios y Balances" en Parametros Principales de Contabilidad para esta Compañía')
		sql = """
			SELECT 
			'{period_code}' as campo1,
			'{catalog_fs_bi}'as campo2,	
			ati.code as campo3, 
			sum(case when ati.group_balance in ('B1','B2') then aml.debit-aml.credit else aml.credit-aml.debit end) as campo4,		
			'1'::varchar as campo5,
			NULL as campo6
			FROM account_move_line aml 
			LEFT JOIN account_move am ON am.id =  aml.move_id
			LEFT JOIN account_account aa ON aa.id = aml.account_id 
			LEFT JOIN account_type_it ati ON ati.id = aa.account_type_it_id
			WHERE am.state = 'posted' 
			AND (am.date BETWEEN '{date_start}' AND '{date_end}')
			AND ((CASE
                    WHEN am.is_opening_close = true AND to_char(am.date::timestamp with time zone, 'mmdd'::text) = '0101'::text THEN (to_char(am.date::timestamp with time zone, 'yyyy'::text) || '00'::text)::integer
                    WHEN am.is_opening_close = true AND to_char(am.date::timestamp with time zone, 'mmdd'::text) = '1231'::text THEN (to_char(am.date::timestamp with time zone, 'yyyy'::text) || '13'::text)::integer
                    ELSE to_char(am.date::timestamp with time zone, 'yyyymm'::text)::integer
                END) BETWEEN {period_start} and {period_end})
			AND am.company_id = {company}
			AND aml.display_type IS NULL
			AND ati.code is not null
			AND ati.group_balance is not null
			GROUP BY ati.code
			UNION ALL 
			SELECT 
			'{period_code}' as campo1,
			'{catalog_fs_bi}'as campo2,	
			ati.total_code_sunat as campo3, 
			sum(case when ati.group_balance in ('B1','B2') then aml.debit-aml.credit else aml.credit-aml.debit end) as campo4,		
			'1'::varchar as campo5,
			NULL as campo6
			FROM account_move_line aml 
			LEFT JOIN account_move am ON am.id =  aml.move_id
			LEFT JOIN account_account aa ON aa.id = aml.account_id 
			LEFT JOIN account_type_it ati ON ati.id = aa.account_type_it_id
			WHERE am.state = 'posted' 
			AND (am.date BETWEEN '{date_start}' AND '{date_end}')
			AND ((CASE
                    WHEN am.is_opening_close = true AND to_char(am.date::timestamp with time zone, 'mmdd'::text) = '0101'::text THEN (to_char(am.date::timestamp with time zone, 'yyyy'::text) || '00'::text)::integer
                    WHEN am.is_opening_close = true AND to_char(am.date::timestamp with time zone, 'mmdd'::text) = '1231'::text THEN (to_char(am.date::timestamp with time zone, 'yyyy'::text) || '13'::text)::integer
                    ELSE to_char(am.date::timestamp with time zone, 'yyyymm'::text)::integer
                END) BETWEEN {period_start} and {period_end})
			AND am.company_id = {company}
			AND aml.display_type IS NULL
			AND ati.total_code_sunat is not null
			AND ati.group_balance is not null
			GROUP BY ati.total_code_sunat
			""".format(
				catalog_fs_bi = catalog_fs_bi,
				period_code = str(period.date_start.year)+str('{:02d}'.format(period.date_start.month))+(str('{:02d}'.format(period.date_end.day)) if cc not in ('05','06','07') else str('{:02d}'.format(date.day))),
				company = company_id,
				date_start = fields.Date.to_string(period.date_start.replace(month=1, day=1)),
				date_end = period.date_end.strftime('%Y-%m-%d'),
				period_start = str(period.date_start.year)+'00',
				period_end = period.code
			)
		return sql
	
	def _get_sql_031800(self,period,company_id,cc,date):
		catalog_fs_bi = self.env['account.main.parameter'].search([('company_id','=',company_id)],limit=1).catalog_fs_bi
		if not catalog_fs_bi:
			raise UserError(u'Es necesario configurar el campo "Catálogo de Estados Financieros" en la pestaña "Libros de Inventarios y Balances" en Parametros Principales de Contabilidad para esta Compañía')
		sql = """
			SELECT 
			'{period_code}' as campo1,
			'{catalog_fs_bi}'as campo2,	
			aet.code as campo3, 
			sum(aml.debit-aml.credit) as campo4,		
			'1'::varchar as campo5,
			NULL as campo6
			FROM account_move_line aml 
			LEFT JOIN account_move am ON am.id =  aml.move_id
			LEFT JOIN account_account aa ON aa.id = aml.account_id 
			LEFT JOIN account_efective_type aet ON aet.id = aa.account_type_cash_id
			WHERE am.state = 'posted' 
			AND (am.date BETWEEN '{date_start}' AND '{date_end}')
			AND ((CASE
                    WHEN am.is_opening_close = true AND to_char(am.date::timestamp with time zone, 'mmdd'::text) = '0101'::text THEN (to_char(am.date::timestamp with time zone, 'yyyy'::text) || '00'::text)::integer
                    WHEN am.is_opening_close = true AND to_char(am.date::timestamp with time zone, 'mmdd'::text) = '1231'::text THEN (to_char(am.date::timestamp with time zone, 'yyyy'::text) || '13'::text)::integer
                    ELSE to_char(am.date::timestamp with time zone, 'yyyymm'::text)::integer
                END) BETWEEN {period_start} and {period_end})
			AND am.company_id = {company}
			AND aml.display_type IS NULL
			AND aet.code is not null
			GROUP BY aet.code
			""".format(
				catalog_fs_bi = catalog_fs_bi,
				period_code = str(period.date_start.year)+str('{:02d}'.format(period.date_start.month))+(str('{:02d}'.format(period.date_end.day)) if cc not in ('05','06','07') else str('{:02d}'.format(date.day))),
				company = company_id,
				date_start = fields.Date.to_string(period.date_start.replace(month=1, day=1)),
				date_end = period.date_end.strftime('%Y-%m-%d'),
				period_start = str(period.date_start.year)+'00',
				period_end = period.code
			)
		return sql
	
	def _get_sql_031900(self,period,company_id,cc,date):
		catalog_fs_bi = self.env['account.main.parameter'].search([('company_id','=',company_id)],limit=1).catalog_fs_bi
		if not catalog_fs_bi:
			raise UserError(u'Es necesario configurar el campo "Catálogo de Estados Financieros" en la pestaña "Libros de Inventarios y Balances" en Parametros Principales de Contabilidad para esta Compañía')
		sql = """
				SELECT 
				'{period_code}' as campo1,
				'{catalog_fs_bi}'as campo2,
				sp.code as campo3,
				sp.capital as campo4,
				sp.acc_inv as campo5,
				sp.cap_add as campo6,
				sp.res_no_real as campo7,
				sp.reserv_leg as campo8,
				sp.o_reverv as campo9,
				sp.res_acum as campo10,
				sp.dif_conv as campo11,
				sp.ajus_patr as campo12,
				sp.res_neto_ej as campo13,
				sp.exc_rev as campo14,
				sp.res_ejerc as campo15,
				sp.state as campo16,
				NULL as campo17
				FROM account_sunat_state_patrimony sp
				WHERE (sp.date between '{date_start}' and '{date_end}')  
				AND sp.company_id = {company}
				""".format(
					company = company_id,
					period_code = str(period.date_start.year)+str('{:02d}'.format(period.date_start.month))+(str('{:02d}'.format(period.date_end.day)) if cc not in ('05','06','07') else str('{:02d}'.format(date.day))),
					date_start = period.fiscal_year_id.date_from.strftime('%Y/%m/%d'),
					date_end = period.date_end.strftime('%Y/%m/%d'),
					catalog_fs_bi = catalog_fs_bi,
				)
		
		return sql
	
	def _get_sql_032000(self,period,company_id,cc,date):
		catalog_fs_bi = self.env['account.main.parameter'].search([('company_id','=',company_id)],limit=1).catalog_fs_bi
		if not catalog_fs_bi:
			raise UserError(u'Es necesario configurar el campo "Catálogo de Estados Financieros" en la pestaña "Libros de Inventarios y Balances" en Parametros Principales de Contabilidad para esta Compañía')
		sql = """
			SELECT 
			'{period_code}' as campo1,
			'{catalog_fs_bi}'as campo2,	
			ati.code as campo3, 
			sum(aml.debit-aml.credit) as campo4,		
			'1'::varchar as campo5,
			NULL as campo6
			FROM account_move_line aml 
			LEFT JOIN account_move am ON am.id =  aml.move_id
			LEFT JOIN account_account aa ON aa.id = aml.account_id 
			LEFT JOIN account_type_it ati ON ati.id = aa.account_type_it_id
			WHERE am.state = 'posted' 
			AND (am.date BETWEEN '{date_start}' AND '{date_end}')
			AND ((CASE
                    WHEN am.is_opening_close = true AND to_char(am.date::timestamp with time zone, 'mmdd'::text) = '0101'::text THEN (to_char(am.date::timestamp with time zone, 'yyyy'::text) || '00'::text)::integer
                    WHEN am.is_opening_close = true AND to_char(am.date::timestamp with time zone, 'mmdd'::text) = '1231'::text THEN (to_char(am.date::timestamp with time zone, 'yyyy'::text) || '13'::text)::integer
                    ELSE to_char(am.date::timestamp with time zone, 'yyyymm'::text)::integer
                END) BETWEEN {period_start} and {period_end})
			AND am.company_id = {company}
			AND aml.display_type IS NULL
			AND ati.code is not null
			AND ati.group_function is not null
			GROUP BY ati.code
			""".format(
				catalog_fs_bi = catalog_fs_bi,
				period_code = str(period.date_start.year)+str('{:02d}'.format(period.date_start.month))+(str('{:02d}'.format(period.date_end.day)) if cc not in ('05','06','07') else str('{:02d}'.format(date.day))),
				company = company_id,
				date_start = fields.Date.to_string(period.date_start.replace(month=1, day=1)),
				date_end = period.date_end.strftime('%Y-%m-%d'),
				period_start = str(period.date_start.year)+'00',
				period_end = period.code
			)
		return sql
	
	def _get_sql_032400(self,period,company_id,cc,date):
		catalog_fs_bi = self.env['account.main.parameter'].search([('company_id','=',company_id)],limit=1).catalog_fs_bi
		if not catalog_fs_bi:
			raise UserError(u'Es necesario configurar el campo "Catálogo de Estados Financieros" en la pestaña "Libros de Inventarios y Balances" en Parametros Principales de Contabilidad para esta Compañía')
		sql = """
				SELECT 
				'{period_code}' as campo1,
				'{catalog_fs_bi}'as campo2,
				ir.code as campo3,
				ir.amount as campo4,
				ir.state as campo5,
				NULL as campo6
				FROM account_sunat_integrated_results ir
				WHERE (ir.date between '{date_start}' and '{date_end}')  
				AND ir.company_id = {company}
				""".format(
					company = company_id,
					period_code = str(period.date_start.year)+str('{:02d}'.format(period.date_start.month))+(str('{:02d}'.format(period.date_end.day)) if cc not in ('05','06','07') else str('{:02d}'.format(date.day))),
					date_start = period.fiscal_year_id.date_from.strftime('%Y/%m/%d'),
					date_end = period.date_end.strftime('%Y/%m/%d'),
					catalog_fs_bi = catalog_fs_bi,
				)
		
		return sql
	
	def _get_sql_032500(self,period,company_id,cc,date):
		catalog_fs_bi = self.env['account.main.parameter'].search([('company_id','=',company_id)],limit=1).catalog_fs_bi
		if not catalog_fs_bi:
			raise UserError(u'Es necesario configurar el campo "Catálogo de Estados Financieros" en la pestaña "Libros de Inventarios y Balances" en Parametros Principales de Contabilidad para esta Compañía')
		sql = """
				SELECT 
				'{period_code}' as campo1,
				'{catalog_fs_bi}'as campo2,
				ef.code as campo3,
				ef.amount as campo4,
				ef.state as campo5,
				NULL as campo6
				FROM account_sunat_efective_flow ef
				WHERE (ef.date between '{date_start}' and '{date_end}')  
				AND ef.company_id = {company}
				""".format(
					company = company_id,
					period_code = str(period.date_start.year)+str('{:02d}'.format(period.date_start.month))+(str('{:02d}'.format(period.date_end.day)) if cc not in ('05','06','07') else str('{:02d}'.format(date.day))),
					date_start = period.fiscal_year_id.date_from.strftime('%Y/%m/%d'),
					date_end = period.date_end.strftime('%Y/%m/%d'),
					catalog_fs_bi = catalog_fs_bi,
				)
		
		return sql

	def _get_sql_10(self,period,company_id,cc,date):
		sql = """
		SELECT
		'{period}' as campo1,
		aa.code as campo2,
		aa.code_bank as campo3,
		aa.account_number as campo4,
		rc.name AS campo5,
		T.debe as campo6,
		T.haber as campo7,
		'1' as campo8,
		NULL AS campo9
		FROM
		(SELECT vst.account_id,SUM(vst.debe) AS debe,SUM(vst.haber) AS haber FROM get_diariog('{date_start}','{date_end}',{company_id}) vst
		LEFT JOIN account_account aa ON aa.id = vst.account_id
		WHERE LEFT(vst.cuenta,2) = '10'
		GROUP BY vst.account_id)T
		LEFT JOIN account_account aa ON aa.id = T.account_id
		LEFT JOIN res_currency rc ON rc.id = aa.currency_id
		""".format(
				period = str(period.date_start.year)+str('{:02d}'.format(period.date_start.month))+(str('{:02d}'.format(period.date_end.day)) if cc not in ('05','06','07') else str('{:02d}'.format(date.day))),
				date_start = period.fiscal_year_id.date_from.strftime('%Y/%m/%d'),
				date_end = period.date_end.strftime('%Y/%m/%d'),
				company_id = company_id
			)
		return sql

	def _get_sql_account(self,period,company_id,left,cc,date):
		sql = """
		SELECT 
		'%s' as campo1,
		aml.cuo as campo2,
		CASE
			WHEN right(GS.periodo,2) = '00' THEN 'A' || GS.voucher
			WHEN right(GS.periodo,2) = '13' THEN 'C' || GS.voucher
			ELSE 'M' || GS.voucher
		END AS campo3,
		GS.td_partner as campo4,
		GS.doc_partner as campo5,
		GS.partner as campo6,
		TO_CHAR(GS.fecha_doc::DATE, 'dd/mm/yyyy') as campo7,
		GS.saldo_mn as campo8,
		'1' as campo9,
		NULL AS campo10
		FROM get_saldos_sin_cierre('%s','%s',%d) GS
		LEFT JOIN account_move_line aml ON aml.id = GS.move_line_id
		WHERE left(GS.cuenta,2) in (%s) and GS.saldo_mn <> 0
		"""% (str(period.date_start.year)+str('{:02d}'.format(period.date_start.month))+(str('{:02d}'.format(period.date_end.day)) if cc not in ('05','06','07') else str('{:02d}'.format(date.day))),
			period.fiscal_year_id.date_from.strftime('%Y/%m/%d'),
			period.date_end.strftime('%Y/%m/%d'),
			company_id,
			','.join("'%s'"%(i) for i in left))
		return sql

	def _get_sql_19(self,period,company_id,cc,date):
		sql = """
		SELECT 
		'%s' as campo1,
		aml.cuo as campo2,
		CASE
			WHEN right(GS.periodo,2) = '00' THEN 'A' || GS.voucher
			WHEN right(GS.periodo,2) = '13' THEN 'C' || GS.voucher
			ELSE 'M' || GS.voucher
		END AS campo3,
		GS.td_partner as campo4,
		GS.doc_partner as campo5,
		GS.partner as campo6,
		GS.td_sunat as campo7,
		CASE
			WHEN GS.nro_comprobante is null OR GS.nro_comprobante = '' THEN ' '
			WHEN GS.nro_comprobante is not null and position('-' in GS.nro_comprobante::text) <> 0 AND split_part(GS.nro_comprobante, '-', 1) <> '' THEN split_part(GS.nro_comprobante, '-', 1)
			ELSE ' '
		END AS campo8,
		CASE
			WHEN GS.nro_comprobante is null OR GS.nro_comprobante = '' THEN 'SN'
			WHEN GS.nro_comprobante is not null and position('-' in GS.nro_comprobante::text) <> 0 AND split_part(GS.nro_comprobante, '-', 2) <> '' THEN replace(split_part(GS.nro_comprobante, '-', 2),'_','')
			WHEN GS.nro_comprobante is not null and position('-' in GS.nro_comprobante::text) = 0 AND split_part(GS.nro_comprobante, '-', 1) <> '' THEN replace(split_part(GS.nro_comprobante, '-', 1),'_','')
			ELSE 'SN'
		END AS campo9,
		TO_CHAR(GS.fecha_doc::DATE, 'dd/mm/yyyy') as campo10,
		GS.saldo_mn as campo11,
		'1' as campo12,
		NULL AS campo13
		FROM get_saldos_sin_cierre('%s','%s',%d) GS
		LEFT JOIN account_move_line aml ON aml.id = GS.move_line_id
		WHERE left(GS.cuenta,2) = '19' and GS.saldo_mn <> 0
		"""% (str(period.date_start.year)+str('{:02d}'.format(period.date_start.month))+(str('{:02d}'.format(period.date_end.day)) if cc not in ('05','06','07') else str('{:02d}'.format(date.day))),
			period.fiscal_year_id.date_from.strftime('%Y/%m/%d'),
			period.date_end.strftime('%Y/%m/%d'),
			company_id)
		return sql

	def _get_sql_41(self,period,company_id,cc,date):
		sql = """
		SELECT 
		'%s' as campo1,
		aml.cuo as campo2,
		CASE
			WHEN right(GS.periodo,2) = '00' THEN 'A' || GS.voucher
			WHEN right(GS.periodo,2) = '13' THEN 'C' || GS.voucher
			ELSE 'M' || GS.voucher
		END AS campo3,
		GS.cuenta as campo4,
		GS.td_partner as campo5,
		GS.doc_partner as campo6,
		GS.doc_partner as campo7,
		GS.partner as campo8,
		GS.saldo_mn as campo9,
		'1' as campo10,
		NULL AS campo11
		FROM get_saldos_sin_cierre('%s','%s',%d) GS
		LEFT JOIN account_move_line aml ON aml.id = GS.move_line_id
		WHERE left(GS.cuenta,2) = '41' and GS.saldo_mn <> 0
		"""% (str(period.date_start.year)+str('{:02d}'.format(period.date_start.month))+(str('{:02d}'.format(period.date_end.day)) if cc not in ('05','06','07') else str('{:02d}'.format(date.day))),
			period.fiscal_year_id.date_from.strftime('%Y/%m/%d'),
			period.date_end.strftime('%Y/%m/%d'),
			company_id)
		return sql
	
	def _get_sql_42(self,period,company_id,cc,date):
		sql = """
		SELECT 
		'%s' as campo1,
		aml.cuo as campo2,
		CASE
			WHEN right(GS.periodo,2) = '00' THEN 'A' || GS.voucher
			WHEN right(GS.periodo,2) = '13' THEN 'C' || GS.voucher
			ELSE 'M' || GS.voucher
		END AS campo3,
		GS.td_partner as campo4,
		GS.doc_partner as campo5,
		TO_CHAR(GS.fecha_doc::DATE, 'dd/mm/yyyy') as campo6,
		GS.partner as campo7,
		GS.saldo_mn as campo8,
		'1' as campo9,
		NULL AS campo10
		FROM get_saldos_sin_cierre('%s','%s',%d) GS
		LEFT JOIN account_move_line aml ON aml.id = GS.move_line_id
		WHERE left(GS.cuenta,2) in ('42','43') and GS.saldo_mn <> 0
		"""% (str(period.date_start.year)+str('{:02d}'.format(period.date_start.month))+(str('{:02d}'.format(period.date_end.day)) if cc not in ('05','06','07') else str('{:02d}'.format(date.day))),
			period.fiscal_year_id.date_from.strftime('%Y/%m/%d'),
			period.date_end.strftime('%Y/%m/%d'),
			company_id)
		return sql

	def _get_sql_46(self,period,company_id,cc,date):
		sql = """
		SELECT 
		'%s' as campo1,
		aml.cuo as campo2,
		CASE
			WHEN right(GS.periodo,2) = '00' THEN 'A' || GS.voucher
			WHEN right(GS.periodo,2) = '13' THEN 'C' || GS.voucher
			ELSE 'M' || GS.voucher
		END AS campo3,
		GS.td_partner as campo4,
		GS.doc_partner as campo5,
		TO_CHAR(GS.fecha_doc::DATE, 'dd/mm/yyyy') as campo6,
		GS.partner as campo7,
		GS.cuenta as campo8,
		GS.saldo_mn as campo9,
		'1' as campo10,
		NULL AS campo11
		FROM get_saldos_sin_cierre('%s','%s',%d) GS
		LEFT JOIN account_move_line aml ON aml.id = GS.move_line_id
		WHERE left(GS.cuenta,2) in ('46','47') and GS.saldo_mn <> 0
		"""% (str(period.date_start.year)+str('{:02d}'.format(period.date_start.month))+(str('{:02d}'.format(period.date_end.day)) if cc not in ('05','06','07') else str('{:02d}'.format(date.day))),
			period.fiscal_year_id.date_from.strftime('%Y/%m/%d'),
			period.date_end.strftime('%Y/%m/%d'),
			company_id)
		return sql

	def _get_sql_47(self,period,company_id,cc,date):
		sql = """
		SELECT 
		'%s' as campo1,
		aml.cuo as campo2,
		CASE
			WHEN right(GS.periodo,2) = '00' THEN 'A' || GS.voucher
			WHEN right(GS.periodo,2) = '13' THEN 'C' || GS.voucher
			ELSE 'M' || GS.voucher
		END AS campo3,
		GS.td_partner as campo4,
		GS.doc_partner as campo5,
		GS.partner as campo6,
		GS.saldo_mn as campo7,
		'1' as campo8,
		NULL AS campo9
		FROM get_saldos_sin_cierre('%s','%s',%d) GS
		LEFT JOIN account_move_line aml ON aml.id = GS.move_line_id
		WHERE left(GS.cuenta,2) in ('47') and GS.saldo_mn <> 0
		"""% (str(period.date_start.year)+str('{:02d}'.format(period.date_start.month))+(str('{:02d}'.format(period.date_end.day)) if cc not in ('05','06','07') else str('{:02d}'.format(date.day))),
			period.fiscal_year_id.date_from.strftime('%Y/%m/%d'),
			period.date_end.strftime('%Y/%m/%d'),
			company_id)
		return sql

	def _get_sql_37_49(self,period,company_id,cc,date):
		sql = """
		SELECT 
		'%s' as campo1,
		aml.cuo as campo2,
		CASE
			WHEN right(GS.periodo,2) = '00' THEN 'A' || GS.voucher
			WHEN right(GS.periodo,2) = '13' THEN 'C' || GS.voucher
			ELSE 'M' || GS.voucher
		END AS campo3,
		GS.td_partner as campo4,
		GS.doc_partner as campo5,
		GS.partner as campo6,
		GS.saldo_mn as campo7,
		'1' as campo8,
		NULL AS campo9
		FROM get_saldos_sin_cierre('%s','%s',%d) GS
		LEFT JOIN account_move_line aml ON aml.id = GS.move_line_id
		WHERE left(GS.cuenta,2) in ('37','49') and GS.saldo_mn <> 0
		"""% (str(period.date_start.year)+str('{:02d}'.format(period.date_start.month))+(str('{:02d}'.format(period.date_end.day)) if cc not in ('05','06','07') else str('{:02d}'.format(date.day))),
			period.date_start.strftime('%Y/%m/%d'),
			period.date_end.strftime('%Y/%m/%d'),
			company_id)
		return sql

	def _get_sql_20_21(self,period,company_id,cc,date):
		sql = """
			SELECT 
			'{period_code}' as campo1,
			PC.table_13_sunat as campo2,
			sc05.code as campo3,
			PP.default_code as campo4,
			' ' as campo5,
			' ' as campo6,
			PT.name as campo7,
			sc06.code as campo8,
			'1' as campo9,
			case when T2.saldo_fisico <> 0 then round(T2.saldo_fisico::numeric,8) else 0.00::numeric end as campo10,
			case when T2.costo_prom <> 0 then round(T2.costo_prom::numeric,8) else 0.00::numeric end as campo11,
			round(T2.saldo_valorado::numeric,2) as campo12,
			'1' as campo13,
			NULL as campo14
			FROM
			(SELECT T.*,
			CASE WHEN vst_valuation.account_id IS NOT NULL THEN vst_valuation.account_id
			WHEN vst_valuation.category_id IS NOT NULL AND vst_valuation.account_id IS NULL THEN NULL
			ELSE (SELECT account_id FROM vst_property_stock_valuation_account WHERE company_id = {company} LIMIT 1)
			END AS valuation_account_id
			FROM
			(select GKV.almacen, GKV.product_id,
			sum(GKV.ingreso) as ingreso_can,
			sum(GKV.debit) as ingreso_val,
			sum(GKV.salida) as salida_can,
			sum(GKV.credit) as salida_val,
			sum(GKV.ingreso) - sum(GKV.salida) as saldo_fisico,
			sum(GKV.debit) - sum(GKV.credit) as saldo_valorado,
			case when (sum(GKV.ingreso) - sum(GKV.salida)) <> 0 then
			(sum(GKV.debit) - sum(GKV.credit))/(sum(GKV.ingreso) - sum(GKV.salida))
			else 0 end as costo_prom
			from get_kardex_v({date_start_s},{date_end_s},(select array_agg(id) from product_product) ,(select array_agg(id) from stock_location),{company}) GKV
			WHERE (GKV.fecha::date BETWEEN '{date_start}' AND '{date_end}') 
			group by GKV.almacen, GKV.product_id)T
			LEFT JOIN product_product PP ON PP.id = T.product_id
			LEFT JOIN product_template PT ON PT.id = PP.product_tmpl_id
			LEFT JOIN (SELECT category_id,account_id
			FROM vst_property_stock_valuation_account 
			WHERE company_id = {company}) vst_valuation ON vst_valuation.category_id = PT.categ_id)T2
			LEFT JOIN ACCOUNT_ACCOUNT aa ON aa.id = T2.valuation_account_id
			LEFT JOIN product_product PP ON PP.id = T2.product_id
			LEFT JOIN product_template PT ON PT.id = PP.product_tmpl_id
			LEFT JOIN product_category PC on PT.categ_id = PC.id
			LEFT JOIN uom_uom UU on PT.uom_id = UU.id
			LEFT JOIN stock_catalog_05 sc05 on sc05.id = PC.stock_catalog_05_id
			LEFT JOIN stock_catalog_06 sc06 on sc06.id = UU.stock_catalog_06_id
			WHERE left(aa.code,2) in ('20','21')
		""".format(
			company = company_id,
			date_start_s = str(period.date_start.year) + '0101',
			date_end_s = str(period.date_end).replace('-',''),
			date_start = period.date_start.strftime('%Y/%m/%d'),
			date_end = period.date_end.strftime('%Y/%m/%d'),
			period_code = str(period.date_start.year)+str('{:02d}'.format(period.date_start.month))+(str('{:02d}'.format(period.date_end.day)) if cc not in ('05','06','07') else str('{:02d}'.format(date.day)))
		)
		return sql

	def _get_sql_30(self,period,company_id,cc,date):
		sql = """
			select
			'{period_code}' as campo1,
			aml.cuo as campo2,
			CASE
				WHEN right(vst_d.periodo::character varying,2) = '00' THEN 'A' || vst_d.voucher
				WHEN right(vst_d.periodo::character varying,2) = '13' THEN 'C' || vst_d.voucher
				ELSE 'M' || vst_d.voucher
			END AS campo3,
			lit.code_sunat as campo4,
			rp.vat as campo5,
			rp.name as campo6,
			arv.code as campo7,
			arv.name as campo8,
			arv.qty as campo9,
			arv.costo as campo10,
			arv.provision as campo11,
			'1' as campo12,
			NULL AS campo13
			FROM get_diariog('{date_start}','{date_end}',{company}) vst_d
			LEFT JOIN account_move_line aml ON aml.id = vst_d.move_line_id
			LEFT JOIN account_register_values_it arv ON arv.move_id = vst_d.move_id
			LEFT JOIN res_partner rp ON rp.id = arv.partner_id
			LEFT JOIN l10n_latam_identification_type lit ON lit.id = rp.l10n_latam_identification_type_id
			WHERE left(vst_d.cuenta,2) = '30'
		""".format(
			company = company_id,
			date_start = period.date_start.strftime('%Y/%m/%d'),
			date_end = period.date_end.strftime('%Y/%m/%d'),
			period_code = str(period.date_start.year)+str('{:02d}'.format(period.date_start.month))+(str('{:02d}'.format(period.date_end.day)) if cc not in ('05','06','07') else str('{:02d}'.format(date.day)))
		)
		return sql

	def _get_sql_34(self,period,company_id,cc,date):
		sql = """
			SELECT 
			'{period_code}' as campo1,
			CASE WHEN ASS.invoice_id IS NULL THEN ASS.cuo
			ELSE aml.cuo::character varying END as campo2,
			CASE WHEN ASS.invoice_id IS NULL THEN ASS.code_asiento
			ELSE (CASE WHEN am.is_opening_close = true AND to_char(am.date::timestamp with time zone, 'mmdd'::text) = '0101'::text THEN 'A'||am.name
			WHEN am.is_opening_close = true AND to_char(am.date::timestamp with time zone, 'mmdd'::text) = '1231'::text THEN 'C'||am.name
			 ELSE 'M'||am.name END) END as campo3,
			TO_CHAR(ASS.date::DATE, 'dd/mm/yyyy') as campo4,
			aa.code as campo5,
			ASS.name as campo6,
			ASS.value as campo7,
			round(ASSL.depreciated_value::numeric,2) as campo8,
			'1' as campo9,
			NULL AS campo10
			from account_asset_asset ASS
			LEFT JOIN account_asset_category ASCA on ASCA.id = ASS.category_id
			LEFT JOIN account_account aa on aa.id = ASCA.account_asset_id
			LEFT JOIN account_move am on am.id = ASS.invoice_id
			LEFT JOIN account_move_line aml ON aml.move_id = ASS.invoice_id AND aml.asset_category_id = ASS.category_id
			LEFT JOIN account_asset_depreciation_line ASSL ON ASSL.asset_id = ASS.id AND (ASSL.depreciation_date BETWEEN '{date_start}' and '{date_end}')
			WHERE ASS.company_id = {company} and ASS.date <= '{date_end}' and left(aa.code,2) = '34'
		""".format(
			company = company_id,
			date_start = period.date_start.strftime('%Y/%m/%d'),
			date_end = period.date_end.strftime('%Y/%m/%d'),
			period_code = str(period.date_start.year)+str('{:02d}'.format(period.date_start.month))+(str('{:02d}'.format(period.date_end.day)) if cc not in ('05','06','07') else str('{:02d}'.format(date.day)))
		)
		return sql

	def _get_sql_031601(self,period,company_id,cc,date):
		sql = """
			SELECT 
			'{period_code}' as campo1,
			T.importe_cap as campo2,
			T.valor_nominal as campo3,
			T.nro_acc_sus as campo4,
			T.nro_acc_pag as campo5,
			T.state as campo6,
			NULL AS campo7
			FROM account_sunat_capital T
			WHERE (T.date between '{date_start}' and '{date_end}')  
			AND T.company_id = {company}
		""".format(
			company = company_id,
			period_code = str(period.date_start.year)+str('{:02d}'.format(period.date_start.month))+(str('{:02d}'.format(period.date_end.day)) if cc not in ('05','06','07') else str('{:02d}'.format(date.day))),
			date_start = period.fiscal_year_id.date_from.strftime('%Y/%m/%d'),
			date_end = period.date_end.strftime('%Y/%m/%d'),
		)
		return sql
	
	def _get_sql_031602(self,period,company_id,cc,date):
		sql = """
			SELECT 
			'{period_code}' as campo1,
			LT.code_sunat as campo2,
			RP.vat as campo3,
			T.type as campo4,
			left(RP.name,100) as campo5,
			T.num_acciones as campo6,
			(T.percentage)*100 as campo7,
			T.state as campo8,
			NULL AS campo9
			FROM account_sunat_shareholding T
			LEFT JOIN res_partner RP on RP.id = T.partner_id
			LEFT JOIN l10n_latam_identification_type LT ON LT.id = RP.l10n_latam_identification_type_id
			WHERE (T.date between '{date_start}' and '{date_end}')  
			AND T.company_id = {company}
		""".format(
			company = company_id,
			period_code = str(period.date_start.year)+str('{:02d}'.format(period.date_start.month))+(str('{:02d}'.format(period.date_end.day)) if cc not in ('05','06','07') else str('{:02d}'.format(date.day))),
			date_start = period.fiscal_year_id.date_from.strftime('%Y/%m/%d'),
			date_end = period.date_end.strftime('%Y/%m/%d'),
		)
		return sql

	def _get_sql_031700(self,period,company_id,cc,date):
		sql = """
			SELECT 
			'{period_code}' as campo1,
			aa.code as campo2,
			line.si_debe as campo3,
			line.si_haber as campo4,
			line.debe as campo5,
			line.haber as campo6,
			line.suma_debe as campo7,
			line.suma_haber as campo8,
			line.deudor as campo9,
			line.acreedor as campo10,
			coalesce(line.t_debe,0.00)::numeric as campo11,
			coalesce(line.t_haber,0.00)::numeric as campo12,
			line.activo as campo13,
			line.pasivo as campo14,
			line.perdidas as campo15,
			line.ganancias as campo16,
			coalesce(line.adiciones,0.00)::numeric as campo17,
			coalesce(line.deducciones,0.00)::numeric as campo18,
			line.state as campo19,
			NULL AS campo20
			FROM account_sunat_checking_balance_line line
			LEFT JOIN account_sunat_checking_balance T ON T.id = line.main_id
			LEFT JOIN account_account aa on aa.id = line.account_id
			WHERE (T.date between '{date_start}' and '{date_end}')  
			AND T.company_id = {company}
		""".format(
			company = company_id,
			period_code = str(period.date_start.year)+str('{:02d}'.format(period.date_start.month))+(str('{:02d}'.format(period.date_end.day)) if cc not in ('05','06','07') else str('{:02d}'.format(date.day))),
			date_start = period.fiscal_year_id.date_from.strftime('%Y/%m/%d'),
			date_end = period.date_end.strftime('%Y/%m/%d'),
		)
		return sql

	def _get_sql_nom(self,type):
		sql = ""
		nomenclatura = ""
		
		if type == 1:
			sql = self._get_sql_030100(self.period,self.company_id.id,self.cc,self.date)
			nomenclatura = "030100"

		elif type == 2:
			sql = self._get_sql_10(self.period,self.company_id.id,self.cc,self.date)
			nomenclatura = "030200"

		elif type == 3:
			sql = self._get_sql_account(self.period,self.company_id.id,['12'],self.cc,self.date)
			nomenclatura = "030300"

		elif type == 4:
			sql = self._get_sql_account(self.period,self.company_id.id,['14'],self.cc,self.date)
			nomenclatura = "030400"

		elif type == 5:
			sql = self._get_sql_account(self.period,self.company_id.id,['16','17'],self.cc,self.date)
			nomenclatura = "030500"

		elif type == 6:
			sql = self._get_sql_19(self.period,self.company_id.id,self.cc,self.date)
			nomenclatura = "030600"

		elif type == 7:
			sql = self._get_sql_20_21(self.period,self.company_id.id,self.cc,self.date)
			nomenclatura = "030700"

		elif type == 8:
			sql = self._get_sql_30(self.period,self.company_id.id,self.cc,self.date)
			nomenclatura = "030800"

		elif type == 9:
			sql = self._get_sql_34(self.period,self.company_id.id,self.cc,self.date)
			nomenclatura = "030900"
		
		elif type == 10:
			sql = self._get_sql_41(self.period,self.company_id.id,self.cc,self.date)
			nomenclatura = "031100"
		
		elif type == 11:
			sql = self._get_sql_42(self.period,self.company_id.id,self.cc,self.date)
			nomenclatura = "031200"

		elif type == 12:
			sql = self._get_sql_46(self.period,self.company_id.id,self.cc,self.date)
			nomenclatura = "031300"
		
		elif type == 13:
			sql = self._get_sql_47(self.period,self.company_id.id,self.cc,self.date)
			nomenclatura = "031400"

		elif type == 14:
			sql = self._get_sql_37_49(self.period,self.company_id.id,self.cc,self.date)
			nomenclatura = "031500"

		elif type == 15:
			sql = self._get_sql_031601(self.period,self.company_id.id,self.cc,self.date)
			nomenclatura = "031601"

		elif type == 16:
			sql = self._get_sql_031602(self.period,self.company_id.id,self.cc,self.date)
			nomenclatura = "031602"

		elif type == 17:
			sql = self._get_sql_031700(self.period,self.company_id.id,self.cc,self.date)
			nomenclatura = "031700"

		elif type == 18:
			sql = self._get_sql_031800(self.period,self.company_id.id,self.cc,self.date)
			nomenclatura = "031800"
		elif type == 19:
			sql = self._get_sql_031900(self.period,self.company_id.id,self.cc,self.date)
			nomenclatura = "031900"
		elif type == 20:
			sql = self._get_sql_032000(self.period,self.company_id.id,self.cc,self.date)
			nomenclatura = "032000"
		elif type == 21:
			sql = self._get_sql_032400(self.period,self.company_id.id,self.cc,self.date)
			nomenclatura = "032400"
		elif type == 22:
			sql = self._get_sql_032500(self.period,self.company_id.id,self.cc,self.date)
			nomenclatura = "032500"

		return sql,nomenclatura

	def _get_ple(self,type):
		use_balance_inventory_kardex = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).use_balance_inventory_kardex
		ruc = self.company_id.partner_id.vat
		mond = self.company_id.currency_id.name

		if not ruc:
			raise UserError('No configuro el RUC de su Compañia.')

		if not mond:
			raise UserError('No configuro la moneda de su Compañia.')

		#LE + RUC + AÑO(YYYY) + MES(MM) + DIA(00) 
		name_doc = "LE"+str(ruc)+str(self.period.date_start.year)+str('{:02d}'.format(self.period.date_start.month))+(str('{:02d}'.format(self.period.date_end.day)) if self.cc not in ('05','06','07') else str('{:02d}'.format(self.date.day)))

		che = True
		sql_ple,nomenclatura = self._get_sql_nom(type)
		if type == 7 and not use_balance_inventory_kardex:
			che = False
		self.env.cr.execute(sql_ple)
		sql_ple = "COPY (%s) TO STDOUT WITH %s" % (sql_ple, "CSV DELIMITER '|'")

		try:
			output = BytesIO()
			self.env.cr.copy_expert(sql_ple, output)
			res = base64.b64encode(output.getvalue())
			output.close()
		finally:
			res = res.decode('utf-8')

		# IDENTIFICADOR DEL LIBRO

		name_doc += nomenclatura

		# CODIGO DE OPORTUNIDAD DE PRESENTACION DEL EEFF (cc) +
		# INDICADOR DE OPERACIONES (1) +
		# INDICADOR DE CONTENIDO Con informacion(1), Sin informacion(0) +
		# INDICADOR DE MONEDA UTILIZADA Nuevos Soles(1), US Dolares(2) +
		# INDICADOR DE LIBRO ELECTRONICO GENERADO POR EL PLE (1)

		name_doc += self.cc+"1"+("1" if len(res) > 0 and che else "0") + ("1" if mond == 'PEN' else "2") + "1.txt"
		return name_doc,(res if res and che else base64.b64encode(b'==Sin Registros==').decode('utf-8'))