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
	#show_21 = fields.Boolean(string=u'3.23 - NOTAS A LOS ESTADOS FINANCIEROS',default=False)
	show_22 = fields.Boolean(string=u'3.24 - ESTADO DE RESULTADOS INTEGRALES',default=False)
	show_23 = fields.Boolean(string=u'3.25 - ESTADO DE FLUJOS DE EFECTIVO - MÉTODO INDIRECTO',default=False)

	@api.onchange('show_all')
	def action_add_all(self):
		self.show_1 = self.show_all
		self.show_2 = self.show_all
		self.show_3 = self.show_all
		self.show_4 = self.show_all
		self.show_5 = self.show_all
		self.show_6 = self.show_all
		self.show_7 = self.show_all
		self.show_8 = self.show_all
		self.show_9 = self.show_all
		self.show_10 = self.show_all
		self.show_11 = self.show_all
		self.show_12 = self.show_all
		self.show_13 = self.show_all
		self.show_14 = self.show_all
		self.show_15 = self.show_all
		self.show_16 = self.show_all
		self.show_17 = self.show_all
		self.show_18 = self.show_all
		self.show_19 = self.show_all
		self.show_20 = self.show_all
		#self.show_21 = self.show_all
		self.show_22 = self.show_all
		self.show_23 = self.show_all

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
		output_name_1,output_file_1 = (self._get_ple(1)) if self.show_1 else (None,None)
		output_name_2,output_file_2 = (self._get_ple(2)) if self.show_2 else (None,None)
		output_name_3,output_file_3 = (self._get_ple(3)) if self.show_3 else (None,None)
		output_name_4,output_file_4 = (self._get_ple(4)) if self.show_4 else (None,None)
		output_name_5,output_file_5 = (self._get_ple(5)) if self.show_5 else (None,None)
		output_name_6,output_file_6 = (self._get_ple(6)) if self.show_6 else (None,None)
		output_name_7,output_file_7 = (self._get_ple(7)) if self.show_7 else (None,None)
		output_name_8,output_file_8 = (self._get_ple(8)) if self.show_8 else (None,None)
		output_name_9,output_file_9 = (self._get_ple(9)) if self.show_9 else (None,None)
		output_name_10,output_file_10 = (self._get_ple(10)) if self.show_10 else (None,None)
		output_name_11,output_file_11 = (self._get_ple(11)) if self.show_11 else (None,None)
		output_name_12,output_file_12 = (self._get_ple(12)) if self.show_12 else (None,None)
		output_name_13,output_file_13 = (self._get_ple(13)) if self.show_13 else (None,None)
		output_name_14,output_file_14 = (self._get_ple(14)) if self.show_14 else (None,None)
		output_name_15,output_file_15 = (self._get_ple(15)) if self.show_15 else (None,None)
		output_name_16,output_file_16 = (self._get_ple(16)) if self.show_16 else (None,None)
		output_name_17,output_file_17 = (self._get_ple(17)) if self.show_17 else (None,None)
		output_name_18,output_file_18 = (self._get_ple(18)) if self.show_18 else (None,None)
		output_name_19,output_file_19 = (self._get_ple(19)) if self.show_19 else (None,None)
		output_name_20,output_file_20 = (self._get_ple(20)) if self.show_20 else (None,None)
		#output_name_21,output_file_21 = self._get_ple(2)
		output_name_22,output_file_22 = (self._get_ple(22)) if self.show_22 else (None,None)
		output_name_23,output_file_23 = (self._get_ple(23)) if self.show_23 else (None,None)
		return self.env['popup.it.balance.inventory'].get_file(output_name_1,output_file_1,
																output_name_2,output_file_2,
																output_name_3,output_file_3,
																output_name_4,output_file_4,
																output_name_5,output_file_5,
																output_name_6,output_file_6,
																output_name_7,output_file_7,
																output_name_8,output_file_8,
																output_name_9,output_file_9,
																output_name_10,output_file_10,
																output_name_11,output_file_11,
																output_name_12,output_file_12,
																output_name_13,output_file_13,
																output_name_14,output_file_14,
																output_name_15,output_file_15,
																output_name_16,output_file_16,
																output_name_17,output_file_17,
																output_name_18,output_file_18,
																output_name_19,output_file_19,
																output_name_20,output_file_20,
																#output_name_21,output_file_21,
																output_name_22,output_file_22,
																output_name_23,output_file_23)

	def _get_sql_1(self,period,libro,company_id):
		if libro=="030100":
			sql = """
			SELECT 
			'{period_code}' as campo1,
			'09'as campo2,	
			ati.code as campo3, 
			sum(main.debit-main.credit) as campo4, 		
			'1'::varchar as campo5,
			NULL as campo6
			FROM (
				SELECT aa.account_type_it_id as id , 
					sum(debit)as debit, 
					sum(credit) as credit  
				FROM account_move_line aml 
				LEFT JOIN account_account aa ON aa.id = aml.account_id 
				WHERE aml.parent_state = 'posted' 
				AND aml.date::date BETWEEN '{date_start}' AND '{date_end}'
				AND aml.company_id = {company}
				AND aa.account_type_it_id is not null
				GROUP BY aa.account_type_it_id) main
			LEFT JOIN account_type_it ati ON ati.id = main.id
			GROUP BY ati.code		
			""".format(
				period_code = str(self.period.date_start.year)+str('{:02d}'.format(self.period.date_start.month))+(str('{:02d}'.format(self.period.date_end.day)) if self.cc not in ('05','06','07') else str('{:02d}'.format(self.date.day))),
				company = company_id,
				date_start = fields.Date.to_string(datetime.today().replace(month=1, day=1)),
				date_end = self.period.date_end.strftime('%Y-%m-%d'),
			)
		elif libro=="031800":
			sql = """
				SELECT 
				'{period_code}' as campo1,
				'09'as campo2,	
				gef.efective_group as campo3,
				gef.total as campo4,
				'1'::varchar as campo5,
				NULL as campo6
				FROM get_efective_flow('{date_start}','{date_end}','{code}',{company}) gef
				""".format(
					period_code = str(self.period.date_start.year)+str('{:02d}'.format(self.period.date_start.month))+(str('{:02d}'.format(self.period.date_end.day)) if self.cc not in ('05','06','07') else str('{:02d}'.format(self.date.day))),
					date_start = fields.Date.to_string(datetime.today().replace(month=1, day=1)),
					date_end = self.period.date_end.strftime('%Y-%m-%d'),
					company = company_id,
					code = period.code[:4]+'00',
				)
		elif libro=="032000":
			period_code = str(self.period.date_start.year) + \
                  str('{:02d}'.format(self.period.date_start.month)) + \
                  (str('{:02d}'.format(self.period.date_end.day)) if self.cc not in ('05','06','07') else str('{:02d}'.format(self.date.day)))

			period_start = self.env['account.period'].search([('code', '=', self.period.code[:4] + '00')], limit=1).code
			period_end = self.period.code
			company_id = self.company_id.id

			sql = f"""
			SELECT
				'{period_code}'::varchar as campo1,
				'09' as campo2,
				at.code as campo3,
				sum(bcr.debe) - sum(bcr.haber) as campo4,
				'1'::varchar as campo5,
				NULL as campo6
			FROM get_bc_register('{period_start}','{period_end}', {company_id}) bcr
			LEFT JOIN account_account aa ON aa.code = bcr.cuenta AND aa.company_id = {company_id}
			LEFT JOIN account_type_it at ON at.id = aa.account_type_it_id
			WHERE at.group_function IS NOT NULL
			GROUP BY at.code
			ORDER BY at.code
			"""
		else:
			sql = """
				SELECT 
				'{period_code}' as campo1,
				'01'as campo2,
				l.code as campo3,
				l.amount as campo4,
				'1' as campo5,
				NULL as campo6
				FROM sunat_table_data_line l
				LEFT JOIN sunat_table_data main on main.id = l.main_id
				LEFT JOIN account_fiscal_year anio on anio.id = main.fiscal_year_id
				WHERE anio.name = '{year}' and main.sunat = '{libro}' and main.company_id = {company}
				""".format(
					company = company_id,
					libro = libro,
					period_code = str(self.period.date_start.year)+str('{:02d}'.format(self.period.date_start.month))+(str('{:02d}'.format(self.period.date_end.day)) if self.cc not in ('05','06','07') else str('{:02d}'.format(self.date.day))),
					year = period.fiscal_year_id.name
				)
		return sql

	def _get_sql_type_19(self,period,libro,company_id):
		sql ="""
			SELECT 
			'{period_code}' as campo1,
			'01'as campo2,
			at.code as campo3,
			SUM(CASE WHEN apt.code='001' THEN -a1.balance ELSE 0 END) AS campo4,
			SUM(CASE WHEN apt.code='002' THEN -a1.balance ELSE 0 END) AS campo5,
			SUM(CASE WHEN apt.code='003' THEN -a1.balance ELSE 0 END) AS campo6,
			SUM(CASE WHEN apt.code='004' THEN -a1.balance ELSE 0 END) AS campo7,
			0 as campo8,
			0 as campo9,
			SUM(CASE WHEN apt.code='007' THEN -a1.balance ELSE 0 END) AS campo10,
			0 as campo11,
			0 as campo12,
			0 as campo13,
			SUM(CASE WHEN apt.code='005' THEN -a1.balance ELSE 0 END) AS campo14,
			SUM(CASE WHEN apt.code='006' THEN -a1.balance ELSE 0 END) AS campo15,
			'1' as campo16,
			NULL as campo17
			FROM get_diariog('{date_start}','{date_end}',{company}) a1
			LEFT JOIN account_account a2 ON a2.id=a1.account_id
			LEFT JOIN  account_patrimony_type apt ON apt.id = a2.patrimony_id
			left join account_type_it at on at.id = a2.account_type_it_id
			WHERE left(a1.cuenta,1)='5' AND (a1.fecha between '{date_start}' AND '{date_end}')
			AND a2.company_id = {company}
			GROUP BY at.code
		""".format(
					period_code = str(self.period.date_start.year)+str('{:02d}'.format(self.period.date_start.month))+(str('{:02d}'.format(self.period.date_end.day)) if self.cc not in ('05','06','07') else str('{:02d}'.format(self.date.day))),
					date_start = fields.Date.to_string(datetime.today().replace(month=1, day=1)),
					date_end = self.period.date_end.strftime('%Y-%m-%d'),
					company = company_id,
				)
		#	sql = """
		#	SELECT 
		#	'{period_code}' as campo1,
		#	'09'as campo2,	
		#	l.code as campo3,
		#	l.capital as campo4,
		#	l.acc_inv as campo5,
		#	l.cap_add as campo6,
		#	l.res_no_real as campo7,
		#	l.reserv_leg as campo8,
		#	l.o_reverv as campo9,
		#	l.res_acum as campo10,
		#	l.dif_conv as campo11,
		#	l.ajus_patr as campo12,
		#	l.res_neto_ej as campo13,
		#	l.exc_rev as campo14,
		#	l.res_ejerc as campo15,
		#	'1' as campo16,
		#	NULL as campo17
		#	FROM account_patrimony_book 
		#	""".format(			
		#		period_code = str(self.period.date_start.year)+str('{:02d}'.format(self.period.date_start.month))+(str('{:02d}'.format(self.period.date_end.day)) if self.cc not in ('05','06','07') else str('{:02d}'.format(self.date.day))),
		#	)
		return sql

	def _get_sql_10(self,period,company_id):
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
				period = period.code+'00',
				date_start = period.fiscal_year_id.date_from.strftime('%Y/%m/%d'),
				date_end = period.date_end.strftime('%Y/%m/%d'),
				company_id = company_id
			)
		return sql

	def _get_sql_account(self,period,company_id,left):
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
		FROM get_saldos('%s','%s',%d) GS 
		LEFT JOIN account_move_line aml ON aml.id = GS.move_line_id
		WHERE left(GS.cuenta,2) in (%s) and GS.saldo_mn <> 0
		"""% (period.code+'00',
			period.date_start.strftime('%Y/%m/%d'),
			period.date_end.strftime('%Y/%m/%d'),
			company_id,
			','.join("'%s'"%(i) for i in left))
		return sql

	def _get_sql_19(self,period,company_id):
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
		FROM get_saldos('%s','%s',%d) GS
		LEFT JOIN account_move_line aml ON aml.id = GS.move_line_id
		WHERE left(GS.cuenta,2) = '19' and GS.saldo_mn <> 0
		"""% (period.code+'00',
			period.date_start.strftime('%Y/%m/%d'),
			period.date_end.strftime('%Y/%m/%d'),
			company_id)
		return sql

	def _get_sql_41(self,period,company_id):
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
		FROM get_saldos('%s','%s',%d) GS
		LEFT JOIN account_move_line aml ON aml.id = GS.move_line_id
		WHERE left(GS.cuenta,2) = '41' and GS.saldo_mn <> 0
		"""% (period.code+'00',
			period.date_start.strftime('%Y/%m/%d'),
			period.date_end.strftime('%Y/%m/%d'),
			company_id)
		return sql
	
	def _get_sql_42(self,period,company_id):
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
		FROM get_saldos('%s','%s',%d) GS
		LEFT JOIN account_move_line aml ON aml.id = GS.move_line_id
		WHERE left(GS.cuenta,2) in ('42','43') and GS.saldo_mn <> 0
		"""% (period.code+'00',
			period.date_start.strftime('%Y/%m/%d'),
			period.date_end.strftime('%Y/%m/%d'),
			company_id)
		return sql

	def _get_sql_46(self,period,company_id):
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
		FROM get_saldos('%s','%s',%d) GS
		LEFT JOIN account_move_line aml ON aml.id = GS.move_line_id
		WHERE left(GS.cuenta,2) in ('46','47') and GS.saldo_mn <> 0
		"""% (period.code+'00',
			period.date_start.strftime('%Y/%m/%d'),
			period.date_end.strftime('%Y/%m/%d'),
			company_id)
		return sql

	def _get_sql_47(self,period,company_id):
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
		FROM get_saldos('%s','%s',%d) GS
		LEFT JOIN account_move_line aml ON aml.id = GS.move_line_id
		WHERE left(GS.cuenta,2) in ('47') and GS.saldo_mn <> 0
		"""% (period.code+'00',
			period.date_start.strftime('%Y/%m/%d'),
			period.date_end.strftime('%Y/%m/%d'),
			company_id)
		return sql

	def _get_sql_37_49(self,period,company_id):
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
		FROM get_saldos('%s','%s',%d) GS
		LEFT JOIN account_move_line aml ON aml.id = GS.move_line_id
		WHERE left(GS.cuenta,2) in ('47') and GS.saldo_mn <> 0
		"""% (period.code+'00',
			period.date_start.strftime('%Y/%m/%d'),
			period.date_end.strftime('%Y/%m/%d'),
			company_id)
		return sql

	def _get_sql_20_21(self,period,company_id):
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
			period_code = str(self.period.date_start.year)+str('{:02d}'.format(self.period.date_start.month))+(str('{:02d}'.format(self.period.date_end.day)) if self.cc not in ('05','06','07') else str('{:02d}'.format(self.date.day)))
		)
		return sql

	def _get_sql_30(self,period,company_id):
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
			period_code = period.code + '00'
		)
		return sql

	def _get_sql_34(self,period,company_id):
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
			period_code = period.code + '00'
		)
		return sql

	def _get_sql_031601(self,period,company_id):
		sql = """
			SELECT 
			'{period_code}' as campo1,
			T.importe_cap as campo2,
			T.valor_nominal as campo3,
			T.nro_acc_sus as campo4,
			T.nro_acc_pag as campo5,
			T.estado as campo6,
			NULL AS campo7
			FROM sunat_table_data_031601 T
			LEFT JOIN account_fiscal_year Y on Y.id = T.fiscal_year_id
			WHERE Y.name = '{year}' AND T.company_id = {company}
		""".format(
			company = company_id,
			period_code = period.code + '00',
			year = period.code[:4]
		)
		return sql
	
	def _get_sql_031602(self,period,company_id):
		sql = """
			SELECT 
			'{period_code}' as campo1,
			LT.code_sunat as campo2,
			RP.vat as campo3,
			T.tipo as campo4,
			RP.name as campo5,
			T.num_acciones as campo6,
			(T.percentage)*100 as campo7,
			T.estado as campo8,
			NULL AS campo9
			FROM sunat_table_data_031602 T
			LEFT JOIN account_fiscal_year Y on Y.id = T.fiscal_year_id
			LEFT JOIN res_partner RP on RP.id = T.partner_id
			LEFT JOIN l10n_latam_identification_type LT ON LT.id = RP.l10n_latam_identification_type_id
			WHERE Y.name = '{year}' AND T.company_id = {company}
		""".format(
			company = company_id,
			period_code = period.code + '00',
			year = period.code[:4]
		)
		return sql

	def _get_sql_031700(self,period,company_id):
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
			line.t_debe as campo11,
			line.t_haber as campo12,
			line.activo as campo13,
			line.pasivo as campo14,
			line.perdidas as campo15,
			line.ganancias as campo16,
			line.adiciones as campo17,
			line.deducciones as campo18,
			line.estado as campo19,
			NULL AS campo20
			FROM sunat_table_data_031700_line line
			LEFT JOIN sunat_table_data_031700 T ON T.id = line.main_id
			LEFT JOIN account_fiscal_year Y on Y.id = T.fiscal_year_id
			LEFT JOIN account_account aa on aa.id = line.account_id
			WHERE Y.name = '{year}' AND T.company_id = {company}
		""".format(
			company = company_id,
			period_code = period.code + '00',
			year = period.code[:4]
		)
		return sql

	def _get_sql_nom(self,type):
		sql = ""
		nomenclatura = ""
		
		if type == 1:
			sql = self._get_sql_1(self.period,"030100",self.company_id.id)
			nomenclatura = "030100"

		elif type == 2:
			sql = self._get_sql_10(self.period,self.company_id.id)
			nomenclatura = "030200"

		elif type == 3:
			sql = self._get_sql_account(self.period,self.company_id.id,['12'])
			nomenclatura = "030300"

		elif type == 4:
			sql = self._get_sql_account(self.period,self.company_id.id,['14'])
			nomenclatura = "030400"

		elif type == 5:
			sql = self._get_sql_account(self.period,self.company_id.id,['16','17'])
			nomenclatura = "030500"

		elif type == 6:
			sql = self._get_sql_19(self.period,self.company_id.id)
			nomenclatura = "030600"

		elif type == 7:
			sql = self._get_sql_20_21(self.period,self.company_id.id)
			nomenclatura = "030700"

		elif type == 8:
			sql = self._get_sql_30(self.period,self.company_id.id)
			nomenclatura = "030800"

		elif type == 9:
			sql = self._get_sql_34(self.period,self.company_id.id)
			nomenclatura = "030900"
		
		elif type == 10:
			sql = self._get_sql_41(self.period,self.company_id.id)
			nomenclatura = "031100"
		
		elif type == 11:
			sql = self._get_sql_42(self.period,self.company_id.id)
			nomenclatura = "031200"

		elif type == 12:
			sql = self._get_sql_46(self.period,self.company_id.id)
			nomenclatura = "031300"
		
		elif type == 13:
			sql = self._get_sql_47(self.period,self.company_id.id)
			nomenclatura = "031400"

		elif type == 14:
			sql = self._get_sql_37_49(self.period,self.company_id.id)
			nomenclatura = "031500"

		elif type == 15:
			sql = self._get_sql_031601(self.period,self.company_id.id)
			nomenclatura = "031601"

		elif type == 16:
			sql = self._get_sql_031602(self.period,self.company_id.id)
			nomenclatura = "031602"

		elif type == 17:
			sql = self._get_sql_031700(self.period,self.company_id.id)
			nomenclatura = "031700"

		elif type == 18:
			sql = self._get_sql_1(self.period,"031800",self.company_id.id)
			nomenclatura = "031800"
		elif type == 19:
			sql = self._get_sql_type_19(self.period,"031900",self.company_id.id)
			nomenclatura = "031900"
		elif type == 20:
			sql = self._get_sql_1(self.period,"032000",self.company_id.id)
			nomenclatura = "032000"
		elif type == 22:
			sql = self._get_sql_1(self.period,"032400",self.company_id.id)
			nomenclatura = "032400"
		elif type == 23:
			sql = self._get_sql_1(self.period,"032500",self.company_id.id)
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
		return name_doc,(res if res and che else base64.encodestring(b"== Sin Registros =="))