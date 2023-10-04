# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError
import base64

class AccountSunatWizard(models.TransientModel):
	_inherit = 'account.sunat.wizard'

	def get_txt_retenciones(self):
		retention_journal_id = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).retention_journal_id
		if not retention_journal_id:
			raise UserError(u'Debe configurar su diario de Retenciones en Parametros Principales de Contabilidad para su Compañía.')
		pm = self.env['multipayment.advance.it'].search([('journal_id','=',retention_journal_id.id),('account_date','>=',self.period_id.date_start),('account_date','<=',self.period_id.date_end)])
		pm.compute_amount_cash()
		ruc = self.company_id.partner_id.vat

		if not ruc:
			raise UserError('No configuro el RUC de su Compañia.')

		#0621 + RUC + AÑO(YYYY) + MES(MM) + R.txt
		name_doc = "0621"+str(ruc)+str(self.period_id.date_start.year)+str('{:02d}'.format(self.period_id.date_start.month))+"R.txt"

		sql_query = self._get_sql_txt_retenciones(retention_journal_id)
		ReportBase = self.env['report.base']
		res = ReportBase.get_file_sql_export(sql_query,'|')

		return self.env['popup.it'].get_file(name_doc,res)
	
	def _get_sql_txt_retenciones(self,retention_journal_id):
		
		sql = """
			SELECT rp.vat as campo1,
			CASE
				WHEN split_part(mp.nro_operation::text, '-'::text, 2) <> ''::text THEN split_part(mp.nro_operation::text, '-'::text, 1)::character varying
				ELSE ''::character varying
			END AS campo2,
			CASE
				WHEN split_part(mp.nro_operation::text, '-'::text, 2) <> ''::text THEN split_part(mp.nro_operation::text, '-'::text, 2)::character varying
				ELSE split_part(mp.nro_operation::text, '-'::text, 1)::character varying
			END AS campo3,
			TO_CHAR(mp.payment_date :: DATE, 'dd/mm/yyyy') as campo4,
			mp.amount as campo5,
			ec01.code as campo6,
			CASE
				WHEN split_part(aml.nro_comp::text, '-'::text, 2) <> ''::text THEN split_part(aml.nro_comp::text, '-'::text, 1)::character varying
				ELSE ''::character varying
			END as campo7,
			CASE
				WHEN split_part(aml.nro_comp::text, '-'::text, 2) <> ''::text THEN split_part(aml.nro_comp::text, '-'::text, 2)::character varying
				ELSE split_part(aml.nro_comp::text, '-'::text, 1)::character varying
			END AS campo8,
			TO_CHAR(am.invoice_date :: DATE, 'dd/mm/yyyy') as campo9,
			am.amount_total_signed as campo10,
			NULL AS campo11	
			from multipayment_advance_it mp
			left join res_partner rp on rp.id = mp.partner_cash_id
			left join multipayment_advance_it_line mpl on mpl.main_id = mp.id
			left join account_move_line aml on aml.id = mpl.invoice_id
			left join account_move am on am.id = aml.move_id
			LEFT JOIN l10n_latam_document_type ec01 ON ec01.id = am.l10n_latam_document_type_id
			where (mp.account_date between '%s' and '%s') and mp.company_id = %d and mp.journal_id = %d and mp.state = 'done'
		"""%(self.period_id.date_start.strftime('%Y/%m/%d'),
				self.period_id.date_end.strftime('%Y/%m/%d'),
				self.company_id.id,
				retention_journal_id.id)
		return sql
