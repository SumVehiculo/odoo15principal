# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError
import base64
from datetime import datetime, timedelta

class AccountCashFlowRep(models.TransientModel):
	_name = 'account.cash.flow.rep'

	name = fields.Char()
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	period_id = fields.Many2one('account.period',string=u'Periodo',required=True)

	def get_report(self):
		self.env.cr.execute("""DELETE FROM account_cash_flow_book WHERE user_id = %d"""%(self.env.uid))
	
		self.env.cr.execute("""
			INSERT INTO account_cash_flow_book (grupo,concepto,account_id,fecha,amount,semana,user_id) 
			("""+self._get_sql()+""")""")
		
		return {
				'name': 'Reporte de Flujo de Caja',
				'type': 'ir.actions.act_window',
				'res_model': 'account.cash.flow.book',
				'view_mode': 'tree,pivot,graph',
				'view_type': 'form',
			}


	def _get_sql(self):

		sql_case = ""
		for week in self.get_weeks_from_month(self.period_id.date_start,self.period_id.date_end):
			sql_case += " WHEN (T.fecha BETWEEN '%s' and '%s') THEN '%s' \n"%(week[0].strftime('%Y/%m/%d'),week[1].strftime('%Y/%m/%d'),week[2])

		sql = """SELECT 
				CASE WHEN T.grupo = '1' THEN '1-SALDO INICIAL'
				WHEN T.grupo = '2' THEN '2-INGRESO'
				WHEN T.grupo = '3' THEN '3-EGRESO'
				WHEN T.grupo = '4' THEN '4-FINANCIAMIENTO' END AS grupo,
				T.concepto,
				T.account_id,
				T.fecha,
				T.amount,
				CASE %s END AS semana,
				'%d' AS user_id
				FROM (SELECT 
				acf.grupo,
				acf.code,
				acf.code||'-'||acf.name as concepto,
				aml.account_id,
                '%s'::date as fecha,
				aml.balance as amount
				FROM account_move_line aml
				LEFT JOIN account_account aa ON aa.id = aml.account_id
				LEFT JOIN account_move am ON am.id = aml.move_id
				LEFT JOIN account_cash_flow acf ON acf.id = aa.account_cash_flow_id
				WHERE LEFT(aa.code,2) = '10' AND am.state = 'posted' AND aml.company_id = %d AND aml.display_type IS NULL
				AND (CASE
						WHEN am.is_opening_close = true AND to_char(am.date::timestamp with time zone, 'mmdd'::text) = '0101'::text THEN to_char(am.date::timestamp with time zone, 'yyyy'::text) || '00'::text
						WHEN am.is_opening_close = true AND to_char(am.date::timestamp with time zone, 'mmdd'::text) = '1231'::text THEN to_char(am.date::timestamp with time zone, 'yyyy'::text) || '13'::text
						ELSE to_char(am.date::timestamp with time zone, 'yyyymm'::text)
					END::integer BETWEEN '%s' AND '%d')
					
				UNION ALL

				SELECT 
				acf.grupo,
				acf.code,
				acf.code||'-'||acf.name as concepto,
				aml.account_id,
				am.date as fecha,
				(aml.balance)*-1 as amount
				FROM account_move_line aml
				LEFT JOIN account_account aa ON aa.id = aml.account_id
				LEFT JOIN account_cash_flow acf ON acf.id = aa.account_cash_flow_id
				LEFT JOIN account_move am ON am.id = aml.move_id
				WHERE LEFT(aa.code,2) <> '10' AND aa.account_cash_flow_id IS NOT NULL AND aml.move_id in (
				SELECT
				DISTINCT ON (aml.move_id) move_id
				FROM account_move_line aml
				LEFT JOIN account_account aa ON aa.id = aml.account_id
				LEFT JOIN account_move am ON am.id = aml.move_id
				WHERE am.state = 'posted' AND am.company_id = %d AND aml.display_type IS NULL AND am.is_opening_close <> TRUE 
				AND (am.date BETWEEN '%s' AND '%s')
				AND LEFT(aa.code,2) = '10'))T
				ORDER BY T.grupo,T.code
		""" % (sql_case,
			self.env.uid,
			self.period_id.date_start.strftime('%Y/%m/%d'),
			self.company_id.id,
			self.period_id.fiscal_year_id.name + '00',
			int(self.period_id.code) - 1,
			self.company_id.id,
			self.period_id.date_start.strftime('%Y/%m/%d'),
			self.period_id.date_end.strftime('%Y/%m/%d'))
		
		return sql

	def weekday_it(self,date):
		#DOMINGO 0
		#LUNES 1
		#MARTES 2
		#MIERCOLES 3
		#JUEVES 4
		#VIERNES 5
		#SABADO 6

		if date.weekday() == 6:
			return 0
		else:
			return date.weekday()+1

	def get_weeks_from_month(self,date_from,date_to):
		
		weeks = []
		day = date_from
		cont = 1
		if self.weekday_it(date_from) == 6:
			weeks.append([date_from,date_from,'SEMANA %d'%(cont)])
			day = date_from + timedelta(days=1)
			cont += 1

		while day <= date_to:
			fin = day + timedelta(days=6-self.weekday_it(day))
			if fin.month != date_to.month:
				weeks.append([day,date_to,'SEMANA %d'%(cont)])
			else:
				weeks.append([day,fin,'SEMANA %d'%(cont)])
			day = day + timedelta(days=7-self.weekday_it(day))
			cont += 1

		return weeks
		#for we in weeks:
		#	print(we[0].strftime('%Y/%m/%d') + '-' + we[1].strftime('%Y/%m/%d')+'-'+we[2])
