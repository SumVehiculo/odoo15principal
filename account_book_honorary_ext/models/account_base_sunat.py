# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime, timedelta
from odoo.exceptions import UserError
import base64

class AccountBaseSunat(models.Model):
	_inherit = 'account.base.sunat'

	def _get_sql(self,type,period_id,company_id):
		sql, nomenclatura = super(AccountBaseSunat,self)._get_sql(type,period_id,company_id)
		if type == 7:
			#SQL Rec de Honorarios
			sql = """select 
				row_number() OVER () AS id,
				tt.periodo,
				tt.libro,
				tt.voucher,
				tt.fecha_e,
				tt.fecha_p,
				tt.td,
				tt.serie,
				tt.numero,
				tt.tdp,
				tt.docp,
				tt.apellido_p,
				tt.apellido_m,
				tt.namep,
				tt.divisa,
				tt.tipo_c,
				tt.renta,
				tt.retencion,
				tt.neto_p,
				tt.periodo_p,
				tt.is_not_home,
				tt.c_d_imp,
				am.honorary_type
				from get_recxhon_1_1('{date_start}','{date_end}',{company_id},'invoice_date_due') tt
				LEFT JOIN account_move am on am.id = tt.am_id
			""".format(
					date_start = period_id.date_start.strftime('%Y/%m/%d'),
					date_end = period_id.date_end.strftime('%Y/%m/%d'),
					company_id = company_id
				)

		return sql, nomenclatura