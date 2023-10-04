# -*- coding:utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError

class AccountMainParameter(models.Model):
	_inherit = 'account.main.parameter'

	partner_adjustment_id = fields.Many2one('res.partner',string='Partner Ajustes')

	@api.constrains('exchange_difference')
	def contraint_exchange_difference(self):
		if self.exchange_difference:
			self.env.cr.execute("""
			CREATE OR REPLACE FUNCTION public.get_saldos_me_global(
				periodo_apertura character,
				periodo character,
				company_id integer)
				RETURNS TABLE(account_id integer, debe numeric, haber numeric, saldomn numeric, saldome numeric) 
				LANGUAGE 'plpgsql'

				COST 100
				VOLATILE 
				ROWS 1000
			AS $BODY$
			BEGIN
				RETURN QUERY   
				SELECT a1.account_id,
					sum(a1.debe) AS debe,
					sum(a1.haber) AS haber,
					sum(coalesce(a1.balance,0)) AS saldomn,
					sum(coalesce(a1.importe_me,0)) AS saldome
					FROM get_diariog((select date_start from account_period where code = $1::character varying limit 1),(select date_end from account_period where code = $2::character varying  limit 1),$3) a1
					LEFT JOIN account_account a2 ON a2.id = a1.account_id
					LEFT JOIN res_currency a4 on a4.id = a2.currency_id
					WHERE a4.name = 'USD' AND
					a2.is_document_an <> TRUE AND (a1.periodo::integer between $1::integer and $2::integer)
					GROUP BY a1.account_id;
			END;
			$BODY$;

			CREATE OR REPLACE FUNCTION public.get_saldos_me_documento(
				periodo_apertura character,
				periodo character,
				company_id integer)
				RETURNS TABLE(partner_id integer, account_id integer, td_sunat character varying, nro_comprobante character varying, debe numeric, haber numeric, saldomn numeric, saldome numeric) 
				LANGUAGE 'plpgsql'

				COST 100
				VOLATILE 
				ROWS 1000
			AS $BODY$
			BEGIN
				RETURN QUERY   
				select a1.partner_id,
				a1.account_id,
				a1.td_sunat,
				a1.nro_comprobante,
				sum(a1.debe) debe,
				sum(a1.haber) haber,
				sum(coalesce(a1.balance,0))as saldomn,
				sum(coalesce(a1.importe_me,0)) as saldome 
				from get_diariog((select date_start from account_period where code = $1::character varying limit 1),(select date_end from account_period where code = $2::character varying  limit 1),$3) a1
				left join account_account a2 on a2.id=a1.account_id
				left join account_type_it a3 on a3.id=a2.account_type_it_id
				left join res_currency a4 on a4.id = a2.currency_id
				where 
				a2.is_document_an = TRUE and
				a4.name = 'USD' and
				(a1.periodo::int between $1::int and $2::int)
				group by a1.partner_id,a1.account_id,a1.td_sunat,a1.nro_comprobante
				having (sum(a1.balance)+sum(a1.importe_me)) <> 0;
			END;
			$BODY$;
			""")
		else:
			self.env.cr.execute("""
			CREATE OR REPLACE FUNCTION public.get_saldos_me_global(
				periodo_apertura character,
				periodo character,
				company_id integer)
				RETURNS TABLE(account_id integer, debe numeric, haber numeric, saldomn numeric, saldome numeric) 
				LANGUAGE 'plpgsql'

				COST 100
				VOLATILE 
				ROWS 1000
			AS $BODY$
			BEGIN
				RETURN QUERY   
				SELECT a1.account_id,
					sum(a1.debe) AS debe,
					sum(a1.haber) AS haber,
					sum(coalesce(a1.balance,0)) AS saldomn,
					sum(coalesce(a1.importe_me,0)) AS saldome
					FROM get_diariog((select date_start from account_period where code = $1::character varying limit 1),(select date_end from account_period where code = $2::character varying  limit 1),$3) a1
					LEFT JOIN account_account a2 ON a2.id = a1.account_id
					LEFT JOIN res_currency a4 on a4.id = a2.currency_id
					WHERE a4.name = 'USD' AND
					a2.dif_cambio_type = 'global' AND (a1.periodo::integer between $1::integer and $2::integer)
					GROUP BY a1.account_id;
			END;
			$BODY$;

			CREATE OR REPLACE FUNCTION public.get_saldos_me_documento(
				periodo_apertura character,
				periodo character,
				company_id integer)
				RETURNS TABLE(partner_id integer, account_id integer, td_sunat character varying, nro_comprobante character varying, debe numeric, haber numeric, saldomn numeric, saldome numeric) 
				LANGUAGE 'plpgsql'

				COST 100
				VOLATILE 
				ROWS 1000
			AS $BODY$
			BEGIN
				RETURN QUERY   
				select a1.partner_id,
				a1.account_id,
				a1.td_sunat,
				a1.nro_comprobante,
				sum(a1.debe) debe,
				sum(a1.haber) haber,
				sum(coalesce(a1.balance,0))as saldomn,
				sum(coalesce(a1.importe_me,0)) as saldome 
				from get_diariog((select date_start from account_period where code = $1::character varying limit 1),(select date_end from account_period where code = $2::character varying  limit 1),$3) a1
				left join account_account a2 on a2.id=a1.account_id
				left join account_type_it a3 on a3.id=a2.account_type_it_id
				left join res_currency a4 on a4.id = a2.currency_id
				where 
				a2.dif_cambio_type = 'doc' and
				a4.name = 'USD' and
				(a1.periodo::int between $1::int and $2::int)
				group by a1.partner_id,a1.account_id,a1.td_sunat,a1.nro_comprobante
				having (sum(a1.balance)+sum(a1.importe_me)) <> 0;
			END;
			$BODY$;
			""")
