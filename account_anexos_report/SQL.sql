DROP FUNCTION IF EXISTS public.get_saldos_anexos(date,date,integer,character varying) CASCADE;

CREATE OR REPLACE FUNCTION public.get_saldos_anexos(
	date_from date,
	date_to date,
	id_company integer,
    prefix character varying)
    RETURNS TABLE(id bigint, periodo text, fecha_con text, libro character varying, voucher character varying, td_partner character varying, 
	doc_partner character varying, partner character varying, td_sunat character varying, nro_comprobante character varying, fecha_doc date, 
	fecha_ven date, cuenta character varying, moneda character varying, debe numeric, haber numeric, saldo_mn numeric, saldo_me numeric,
	aml_ids integer[], journal_id integer, account_id integer, partner_id integer, move_id integer, move_line_id integer, company_id integer) 
    LANGUAGE 'plpgsql'
    COST 100
    VOLATILE 
    ROWS 1000
    AS $BODY$
    BEGIN
	RETURN QUERY 
	SELECT row_number() OVER () AS id,t.*
		   FROM ( select 
    CASE
		WHEN am.is_opening_close = true AND to_char(am.date::timestamp with time zone, 'mmdd'::text) = '0101'::text THEN to_char(am.date::timestamp with time zone, 'yyyy'::text) || '00'::text
		WHEN am.is_opening_close = true AND to_char(am.date::timestamp with time zone, 'mmdd'::text) = '1231'::text THEN to_char(am.date::timestamp with time zone, 'yyyy'::text) || '13'::text
		ELSE to_char(am.date::timestamp with time zone, 'yyyymm'::text)
	END AS periodo,
	to_char(am.date::timestamp with time zone, 'yyyy/mm/dd'::text) AS fecha_con,
	aj.code as libro, 
	am.name as voucher, 
	latiden.code_sunat AS td_partner,
	rp.vat as doc_partner, 
	rp.name as partner, 
	ec1.code as td_sunat,
	s.nro_comp as nro_comprobante, 
	am.invoice_date as fecha_doc,
	aml.date_maturity as fecha_ven,
	aa.code as cuenta,
	rc.name as moneda,
	s.debe,s.haber,s.saldo_mn,s.saldo_me ,
	s.aml_ids,
	am.journal_id,
	aml.account_id,
	aml.partner_id,
	aml.move_id,
	s.min as min_line_id,
	am.company_id
	from (SELECT account_move_line.account_id,
    account_move_line.partner_id,
    account_move_line.type_document_id,
    account_move_line.nro_comp,
	array_agg(account_move_line.id) as aml_ids,
    min(account_move_line.id) AS min,
    sum(account_move_line.debit) AS debe,
    sum(account_move_line.credit) AS haber,
    sum(account_move_line.balance) AS saldo_mn,
    sum(account_move_line.amount_currency) AS saldo_me
   FROM account_move_line
	left join account_move am on am.id=account_move_line.move_id
	left join account_account aa on aa.id = account_move_line.account_id
  WHERE left(aa.code,2) = $4
  AND am.state = 'posted' AND (am.date BETWEEN $1 and $2) AND am.company_id = $3
  GROUP BY account_move_line.partner_id, account_move_line.account_id, account_move_line.type_document_id, account_move_line.nro_comp) s
	left join account_move_line aml on aml.id=s.min
	left join account_move am on am.id=aml.move_id
	left join account_account aa on aa.id=s.account_id
	left join account_journal aj on aj.id=am.journal_id
	left join res_partner rp on rp.id=s.partner_id
	LEFT JOIN l10n_latam_identification_type latiden ON latiden.id = rp.l10n_latam_identification_type_id
	LEFT JOIN l10n_latam_document_type ec1 ON ec1.id = aml.type_document_id
	LEFT JOIN res_currency rc ON rc.id = aml.currency_id
	order by rp.vat,aa.code,s.nro_comp) t;
	END;
$BODY$;