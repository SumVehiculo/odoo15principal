# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime, timedelta
from odoo.exceptions import UserError
import base64

class AccountBaseSunat(models.Model):
	_inherit = 'account.base.sunat'

	def _get_sql(self,type,period_id,company_id):
		sql,nomenclatura = super(AccountBaseSunat,self)._get_sql(type=type,period_id=period_id,company_id=company_id)
		if type == 8:
			param = self.env['main.parameter'].search([('company_id','=',company_id)],limit=1)
			if not param.cash_account_prefix_ids:
				raise UserError(u'Debe configurar sus cuentas para Caja en los parametros principales de Contabilidad.')
			sql = """
					SELECT 						
					CASE						
					WHEN right(a1.periodo::character varying,2) = '00' THEN left(a1.periodo::character varying,4) ||'0100'						
					WHEN right(a1.periodo::character varying,2) = '13' THEN left(a1.periodo::character varying,4) ||'1200'						
					ELSE a1.periodo::character varying || '00'						
					END AS campo1,						
					a2.cuo AS campo2,						
					CASE						
					WHEN right(a1.periodo::character varying,2) = '00' THEN 'A' || a1.voucher						
					WHEN right(a1.periodo::character varying,2) = '13' THEN 'C' || a1.voucher						
					ELSE 'M' || a1.voucher						
					END AS campo3,						
					a1.cuenta as campo4,						
					' '::text as campo5,						
					' '::text as campo6,						
					a1.moneda as campo7,						
					a1.td_sunat as campo8,						
					CASE						
					WHEN a1.nro_comprobante is not null and position('-' in a1.nro_comprobante::text) <> 0 THEN split_part(a1.nro_comprobante, '-', 1)						
					ELSE ' '						
					END AS campo9,						
					CASE
					WHEN a1.nro_comprobante is not null and position('-' in a1.nro_comprobante::text) <> 0 THEN split_part(a1.nro_comprobante, '-', 2)						
					WHEN a1.nro_comprobante is not null and position('-' in a1.nro_comprobante::text) = 0 THEN split_part(a1.nro_comprobante, '-', 1)						
					ELSE '0'						
					END AS campo10,						
					TO_CHAR(a1.fecha::DATE, 'dd/mm/yyyy') as campo11,						
					' '::text as campo12,						
					TO_CHAR(a1.fecha::DATE, 'dd/mm/yyyy') as campo13,						
					a1.glosa as campo14,						
					' '::text as campo15,						
					a1.debe as campo16,						
					a1.haber as campo17,						
					' '::text as campo18,						
					a1.ple_diario as campo19,						
					' '::text as campo20						
					FROM get_diariog('{date_start}','{date_end}',{company_id}) a1						
					LEFT JOIN account_move_line a2 on a2.id=a1.move_line_id						
					WHERE a1.periodo='{periodo}' and a1.account_id in ({cash_account_prefix})
			""".format(
					date_start = period_id.date_start.strftime('%Y/%m/%d'),
					date_end = period_id.date_end.strftime('%Y/%m/%d'),
					periodo = period_id.code,
					company_id = company_id,
					cash_account_prefix = ','.join(str(i) for i in param.cash_account_prefix_ids.ids)
				)
			nomenclatura = "010100"

		if type == 9:
			param = self.env['main.parameter'].search([('company_id','=',company_id)],limit=1)
			if not param.bank_account_prefix_ids:
				raise UserError(u'Debe configurar sus cuentas para Banco en los parametros principales de Contabilidad.')
			sql = """
				SELECT 
				CASE
				WHEN right(a1.periodo::character varying,2) = '00' THEN left(a1.periodo::character varying,4) ||'0100'
				WHEN right(a1.periodo::character varying,2) = '13' THEN left(a1.periodo::character varying,4) ||'1200'
				ELSE a1.periodo::character varying || '00'
				END AS campo1,
				a2.cuo AS campo2,
				CASE
				WHEN right(a1.periodo::character varying,2) = '00' THEN 'A' || a1.voucher
				WHEN right(a1.periodo::character varying,2) = '13' THEN 'C' || a1.voucher
				ELSE 'M' || a1.voucher
				END AS campo3,
				a3.code_bank as campo4,
				a3.account_number as campo5,
				TO_CHAR(a1.fecha::DATE, 'dd/mm/yyyy') as campo6,
				a1.medio_pago as campo7,
				a1.glosa as campo8,
				case when coalesce(a1.td_partner,'') = '' then '-' else a1.td_partner end  as campo9,
				case when coalesce(a1.doc_partner,'') = '' then '-' else a1.doc_partner end as campo10,
				case when coalesce(a1.partner,'') = '' then 'VARIOS' else a1.partner end as campo11,
				a1.nro_comprobante as campo12,
				a1.debe as campo13,
				a1.haber as campo14,
				a1.ple_diario as campo15,
				' '::text as campo16
				fROM get_diariog('{date_start}','{date_end}',{company_id}) a1
				LEFT JOIN account_move_line a2 on a2.id=a1.move_line_id
				LEFT JOIN account_account a3 on a3.id=a1.account_id
				WHERE a1.periodo='{periodo}' and a1.account_id in ({bank_account_prefix})
			""".format(
					date_start = period_id.date_start.strftime('%Y/%m/%d'),
					date_end = period_id.date_end.strftime('%Y/%m/%d'),
					periodo = period_id.code,
					company_id = company_id,
					bank_account_prefix = ','.join(str(i) for i in param.bank_account_prefix_ids.ids)
				)
			nomenclatura = "010200"
		return sql,nomenclatura
	
	def pdf_get_sql_vst_caja(self,date_start,date_end,company_id):
		param = self.env['main.parameter'].search([('company_id','=',company_id)],limit=1)
		if not param.cash_account_prefix_ids:
			raise UserError(u'Debe configurar sus cuentas para Caja en los parametros principales de Contabilidad.')
		sql_acc = "'{%s}'" % (','.join(str(i) for i in param.cash_account_prefix_ids.ids))
		sql = """
			SELECT 
			gc.cuenta,
			aa.name as name_cuenta,
			gc.voucher,
			to_char(gc.fecha::timestamp with time zone, 'yyyy/mm/dd'::text) as fecha,
			gc.glosa,
			gc.debe,
			gc.haber
			FROM get_mayorg('{date_from}','{date_to}',{company_id},{sql_acc}) gc
			LEFT JOIN account_account aa ON aa.id = gc.account_id
		
		""".format(
			date_from = date_start.strftime('%Y/%m/%d'),
			date_to = date_end.strftime('%Y/%m/%d'),
			company_id = company_id,
			sql_acc = sql_acc
		)

		return sql
	
	def pdf_get_sql_vst_banco(self,date_start,date_end,company_id):
		param = self.env['main.parameter'].search([('company_id','=',company_id)],limit=1)
		if not param.bank_account_prefix_ids:
			raise UserError(u'Debe configurar sus cuentas para Banco en los parametros principales de Contabilidad.')
		sql_acc = "'{%s}'" % (','.join(str(i) for i in param.bank_account_prefix_ids.ids))
		sql = """
			SELECT 		
			aa.code_bank,	
			aa.account_number,
			gb.cuenta,
			aa.name as nombre_cuenta,
			gb.libro,
			gb.voucher,
			to_char(gb.fecha::timestamp with time zone, 'yyyy/mm/dd'::text) as fecha,
			eip.code as medio_pago,
			gb.glosa,
			gb.partner,
			gb.nro_comprobante,
			gb.debe,
			gb.haber		
			FROM get_mayorg('{date_from}','{date_to}',{company_id},{sql_acc}) gb
			LEFT JOIN account_move am ON am.id = gb.move_id
			LEFT JOIN account_account aa ON aa.id = gb.account_id		
			LEFT JOIN einvoice_catalog_payment eip ON eip.id = am.td_payment_id		
			ORDER BY gb.cuenta,gb.fecha	
		
		""".format(
			date_from = date_start.strftime('%Y/%m/%d'),
			date_to = date_end.strftime('%Y/%m/%d'),
			company_id = company_id,
			sql_acc = sql_acc
		)

		return sql