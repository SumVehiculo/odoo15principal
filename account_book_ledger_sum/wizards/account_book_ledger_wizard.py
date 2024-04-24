# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import date
from odoo.exceptions import UserError
import base64
from io import BytesIO
import re
import uuid

class AccountBookLedgerWizard(models.TransientModel):
	_inherit = 'account.book.ledger.wizard'

	def _get_sql(self):
		sql_accounts = "(select array_agg(id) from account_account where company_id = %d)"%(self.company_id.id)
		if self.content == 'pick':
			if not self.account_ids:
				raise UserError(u'Debe escoger por lo menos una Cuenta')
			sql_accounts = "array[%s] " % (','.join(str(i) for i in self.account_ids.ids))

		sql = """SELECT
			may.periodo::character varying,may.fecha,may.libro,may.voucher,
			may.cuenta,may.debe,may.haber,may.balance, may.saldo,
			may.moneda,may.tc,may.cta_analitica, aat.name as eti_analitica,
			may.glosa,may.td_partner,may.doc_partner,may.partner,
			may.td_sunat,may.nro_comprobante,may.fecha_doc,may.fecha_ven
			FROM get_mayorg('%s','%s',%d,%s) may
			LEFT JOIN (
				select account_move_line_id, min(account_analytic_tag_id) as account_analytic_tag_id 
				from account_analytic_tag_account_move_line_rel
				group by account_move_line_id) rel ON rel.account_move_line_id = may.move_line
			LEFT JOIN account_analytic_tag aat ON aat.id = rel.account_analytic_tag_id
		""" % (self.date_from.strftime('%Y/%m/%d') if self.show_by == 'date' else self.period_from_id.date_start.strftime('%Y/%m/%d'),
			self.date_to.strftime('%Y/%m/%d') if self.show_by == 'date' else self.period_to_id.date_end.strftime('%Y/%m/%d'),
			self.company_id.id,
			sql_accounts)
		return sql
	
	def get_header(self):
		HEADERS = ['PERIODO','FECHA','LIBRO','VOUCHER','CUENTA','DEBE','HABER','BALANCE','SALDO','MON','TC',
				   'CTA ANALITICA',u'ETI. ANALITICA','GLOSA','TDP','RUC','PARTNER','TD','NRO COMPROBANTE','FECHA DOC','FECHA VEN']
		return HEADERS