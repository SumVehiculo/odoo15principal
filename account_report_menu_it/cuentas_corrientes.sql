DROP FUNCTION IF EXISTS public.ctas_ctes(integer) CASCADE;

CREATE OR REPLACE FUNCTION public.ctas_ctes(
	id_company integer)
	RETURNS TABLE(move_line_id integer, move_id integer, account_id integer, partner_id integer, type_document_id integer, nro_comp character varying,
	fecha_emision date, fecha_vencimiento date) 
    LANGUAGE 'plpgsql'
    COST 100
    VOLATILE 
    ROWS 1000
AS $BODY$
BEGIN
	RETURN QUERY 
SELECT min(a1.id) AS move_line_id,
       a2.id AS move_id,
       a1.account_id,
       a1.partner_id,
       a1.type_document_id,
       TRIM(a1.nro_comp)::character varying AS nro_comp,
       min(a1.invoice_date_it) AS fecha_emision,
       max(a1.date_maturity) AS fecha_vencimiento
FROM account_move_line a1
LEFT JOIN account_move a2 ON a2.id = a1.move_id
LEFT JOIN account_account a3 ON a3.id = a1.account_id
WHERE a3.is_document_an = TRUE
  AND a2.state = 'posted'
  AND a1.company_id = $1
  AND a1.cta_cte_origen = TRUE
GROUP BY a1.account_id,
         a1.partner_id,
         a1.type_document_id,
         TRIM(a1.nro_comp),
         a2.id
ORDER BY a2.date;
END;
$BODY$;
----------------------------------------------------------------------------------------------------------------------------------------------
DROP FUNCTION IF EXISTS public.get_saldos(date,date,integer) CASCADE;

CREATE OR REPLACE FUNCTION public.get_saldos(
	date_from date,
	date_to date,
	id_company integer)
	RETURNS TABLE(id bigint, periodo text, fecha_con date, libro character varying, voucher character varying, td_partner character varying, 
	doc_partner character varying, partner character varying, td_sunat character varying, nro_comprobante character varying, fecha_doc date, 
	fecha_ven date, cuenta character varying, moneda character varying, monto_ini_mn numeric, monto_ini_me numeric, debe numeric, haber numeric, saldo_mn numeric, saldo_me numeric,
	aml_ids integer[], journal_id integer, account_id integer, partner_id integer, move_id integer, move_line_id integer, company_id integer) 
	LANGUAGE 'plpgsql'
	COST 100
	VOLATILE 
	ROWS 1000
AS $BODY$
BEGIN
	RETURN QUERY 
	SELECT row_number() OVER () AS id,t.* from 
(select 
CASE
		WHEN am.is_opening_close = true AND to_char((case when b2.fecha_contable is null then am.date else b2.fecha_contable end)::timestamp with time zone, 'mmdd'::text) = '0101'::text THEN to_char((case when b2.fecha_contable is null then am.date else b2.fecha_contable end)::timestamp with time zone, 'yyyy'::text) || '00'::text
		WHEN am.is_opening_close = true AND to_char((case when b2.fecha_contable is null then am.date else b2.fecha_contable end)::timestamp with time zone, 'mmdd'::text) = '1231'::text THEN to_char((case when b2.fecha_contable is null then am.date else b2.fecha_contable end)::timestamp with time zone, 'yyyy'::text) || '13'::text
		ELSE to_char((case when b2.fecha_contable is null then am.date else b2.fecha_contable end)::timestamp with time zone, 'yyyymm'::text)
END AS periodo,
(case when b2.fecha_contable is null then am.date else b2.fecha_contable end)::date AS fecha_con,
aj.code as libro,
am.name as voucher,
lit.code_sunat as td_partner,
rp.vat as doc_partner,
rp.name as partner,
ec1.code as td_sunat,
TRIM(b1.nro_comp)::character varying as nro_comprobante,
b3.fecha_emision::date as fecha_doc,
b3.fecha_vencimiento::date as fecha_ven,
aa.code as cuenta,
case when rc.name is null then 'PEN' else rc.name end as moneda,
b2.monto_ini_mn,
b2.monto_ini_me,
b1.debe,
b1.haber,
b1.saldo_mn,
b1.saldo_me,
b1.aml_ids,
am.journal_id,
b1.account_id,
b1.partner_id,
b3.move_id,
b3.move_line_id,
aml.company_id
from 
(
-- eSTA ES LA CONSULTA QUE RESUME Y SUMA LOS SALDOS DE LOS COMPROBANTES E PAGO SIEMPRE QUE LA CUENTA TENGA MARCADO EL CHECK TIENE ANALISIS DE DOCUMENMTO
select a1.partner_id,a1.account_id,a1.type_document_id,a1.nro_comp,
min(a1.id) as move_line_id,min(a1.move_id) as move_id,	
sum(a1.debit) as debe,sum(a1.credit) as haber,
sum(a1.balance) as saldo_mn,
sum(case when rc.name = 'PEN' then 0 else a1.amount_currency end) as saldo_me,
array_agg(a1.id) as aml_ids
from account_move_line a1
left join account_move a2 on a2.id=a1.move_id
left join account_account a3 on a3.id=a1.account_id
left join res_currency rc on rc.id = a1.currency_id
where a3.is_document_an=TRUE and a2.state='posted' and (a2.date between $1 and $2) and a1.company_id=$3
group by a1.partner_id,a1.account_id,a1.type_document_id,a1.nro_comp)b1

left join
(
select a1.account_id,a1.partner_id,a1.type_document_id,a1.nro_comp,
min(a2.date) as fecha_contable,
sum(a1.debit-a1.credit) as monto_ini_mn,
sum(case when rc.name = 'PEN' then 0 else a1.amount_currency end) as monto_ini_me
from account_move_line a1
left join account_move a2 on a2.id=a1.move_id
left join account_account a3 on a3.id=a1.account_id
left join res_currency rc on rc.id = a1.currency_id
where a2.move_type in ('out_receipt','in_receipt','out_invoice','in_invoice','out_refund','in_refund') and
a3.internal_type in ('payable','receivable') and a2.state='posted' and a1.company_id=$3
group by a1.account_id,a1.partner_id,a1.type_document_id,a1.nro_comp
)b2 on (b2.account_id=b1.account_id and b2.partner_id=b1.partner_id and b2.type_document_id=b1.type_document_id and TRIM(b2.nro_comp)=TRIM(b1.nro_comp))

left join ctas_ctes($3) b3 on (b3.account_id=b1.account_id and b3.partner_id=b1.partner_id and b3.type_document_id=b1.type_document_id and TRIM(b3.nro_comp)=TRIM(b1.nro_comp))
left join account_move_line aml on aml.id=b1.move_line_id
left join account_move am on am.id=b1.move_id
left join res_partner rp on rp.id=b1.partner_id
left join l10n_latam_document_type ec1 on ec1.id=b1.type_document_id
left join account_account aa on aa.id=b1.account_id
left join account_journal aj on aj.id=am.journal_id
left join l10n_latam_identification_type lit on lit.id=rp.l10n_latam_identification_type_id
left join res_currency rc on rc.id=aa.currency_id
order by  aa.code,rp.vat,am.date,ec1.code,b1.nro_comp)t;
END;
$BODY$;
------------------------------------------------------------------------------------------------------------------------------------------
DROP FUNCTION IF EXISTS public.get_saldos_sin_cierre(date,date,integer) CASCADE;

CREATE OR REPLACE FUNCTION public.get_saldos_sin_cierre(
	date_from date,
	date_to date,
	id_company integer)
    RETURNS TABLE(id bigint, periodo text, fecha_con text, libro character varying, voucher character varying, td_partner character varying, 
	doc_partner character varying, partner character varying, td_sunat character varying, nro_comprobante character varying, fecha_doc date, 
	fecha_ven date, cuenta character varying, moneda character varying, monto_ini_mn numeric, monto_ini_me numeric, debe numeric, haber numeric, saldo_mn numeric, saldo_me numeric,
	aml_ids integer[], journal_id integer, account_id integer, partner_id integer, move_id integer, move_line_id integer, company_id integer) 
    LANGUAGE 'plpgsql'
    COST 100
    VOLATILE 
    ROWS 1000
AS $BODY$
BEGIN
	RETURN QUERY 
	SELECT row_number() OVER () AS id,t.* from 
(select 
CASE
		WHEN am.is_opening_close = true AND to_char((case when b2.fecha_contable is null then am.date else b2.fecha_contable end)::timestamp with time zone, 'mmdd'::text) = '0101'::text THEN to_char((case when b2.fecha_contable is null then am.date else b2.fecha_contable end)::timestamp with time zone, 'yyyy'::text) || '00'::text
		WHEN am.is_opening_close = true AND to_char((case when b2.fecha_contable is null then am.date else b2.fecha_contable end)::timestamp with time zone, 'mmdd'::text) = '1231'::text THEN to_char((case when b2.fecha_contable is null then am.date else b2.fecha_contable end)::timestamp with time zone, 'yyyy'::text) || '13'::text
		ELSE to_char((case when b2.fecha_contable is null then am.date else b2.fecha_contable end)::timestamp with time zone, 'yyyymm'::text)
END AS periodo,
to_char((case when b2.fecha_contable is null then am.date else b2.fecha_contable end)::timestamp with time zone, 'yyyy-mm-dd'::text) AS fecha_con,
aj.code as libro,
am.name as voucher,
lit.code_sunat as td_partner,
rp.vat as doc_partner,
rp.name as partner,
ec1.code as td_sunat,
TRIM(b1.nro_comp)::character varying as nro_comprobante,
case when b2.fecha_emision is null then aml.date else b2.fecha_emision end as fecha_doc,
case when b2.fecha_vencimiento is null then aml.date_maturity else b2.fecha_vencimiento end as fecha_ven,
aa.code as cuenta,
case when rc.name is null then 'PEN' else rc.name end as moneda,
b2.monto_ini_mn,
b2.monto_ini_me,
b1.debe,
b1.haber,
b1.saldo_mn,
b1.saldo_me,
b1.aml_ids,
am.journal_id,
b1.account_id,
b1.partner_id,
b1.move_id,
b1.move_line_id,
aml.company_id
from 
(
-- eSTA ES LA CONSULTA QUE RESUME Y SUMA LOS SALDOS DE LOS COMPROBANTES E PAGO SIEMPRE QUE LA CUENTA TENGA MARCADO EL CHECK TIENE ANALISIS DE DOCUMENMTO
select a1.partner_id,a1.account_id,a1.type_document_id,a1.nro_comp,
min(a1.id) as move_line_id,min(a1.move_id) as move_id,	
sum(a1.debit) as debe,sum(a1.credit) as haber,
sum(a1.balance) as saldo_mn,
sum(case when rc.name = 'PEN' then 0 else a1.amount_currency end) as saldo_me,
array_agg(a1.id) as aml_ids
from account_move_line a1
left join account_move a2 on a2.id=a1.move_id
left join account_account a3 on a3.id=a1.account_id
left join res_currency rc on rc.id = a1.currency_id
where a3.is_document_an=TRUE and a2.state='posted' and (a2.date between $1 and $2) and a1.company_id=$3
and (a2.is_opening_close<>TRUE or (a2.is_opening_close = TRUE AND to_char(a2.date::timestamp with time zone, 'mmdd'::text) = '0101'::text))
group by a1.partner_id,a1.account_id,a1.type_document_id,a1.nro_comp)b1

left join
(
select a2.id as move_id,a1.id as move_line_id,a1.account_id,a1.partner_id,a1.type_document_id,a1.nro_comp,
a2.date as fecha_contable,
a2.invoice_date as fecha_emision,
a1.date_maturity as fecha_vencimiento,
a2.glosa as glosa,
a1.debit-a1.credit as monto_ini_mn,case when rc.name = 'PEN' then 0 else a1.amount_currency end as monto_ini_me,
a2.currency_id
from account_move_line a1
left join account_move a2 on a2.id=a1.move_id
left join account_account a3 on a3.id=a1.account_id
left join res_currency rc on rc.id = a1.currency_id
where a2.move_type in ('out_receipt','in_receipt','out_invoice','in_invoice','out_refund','in_refund') and
a3.internal_type in ('payable','receivable') and a2.state='posted' and a1.company_id=$3
)b2 on (b2.account_id=b1.account_id and b2.partner_id=b1.partner_id and b2.type_document_id=b1.type_document_id and TRIM(b2.nro_comp)=TRIM(b1.nro_comp))
left join account_move_line aml on aml.id=b1.move_line_id
left join account_move am on am.id=b1.move_id
left join res_partner rp on rp.id=b1.partner_id
left join l10n_latam_document_type ec1 on ec1.id=b1.type_document_id
left join account_account aa on aa.id=b1.account_id
left join account_journal aj on aj.id=am.journal_id
left join l10n_latam_identification_type lit on lit.id=rp.l10n_latam_identification_type_id
left join res_currency rc on rc.id=aa.currency_id
order by  aa.code,rp.vat,am.date,ec1.code,b1.nro_comp)t;
END;
$BODY$;

---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
DROP FUNCTION IF EXISTS public.get_saldo_detalle(date, date, integer) CASCADE;

CREATE OR REPLACE FUNCTION public.get_saldo_detalle(
	date_from date,
	date_to date,
	company_id integer)
	RETURNS TABLE(periodo character varying, fecha date, libro character varying, voucher character varying,td_partner character varying, doc_partner character varying, partner character varying, td_sunat character varying, nro_comprobante character varying, fecha_doc date, fecha_ven date, cuenta character varying, moneda character varying, debe numeric, haber numeric,balance numeric,importe_me numeric, saldo numeric, saldo_me numeric, partner_id integer, account_id integer) AS
	$BODY$
	BEGIN
	RETURN QUERY 
select 
CASE
	WHEN am.is_opening_close = true AND to_char(am.date::timestamp with time zone, 'mmdd'::text) = '0101'::text THEN (to_char(am.date::timestamp with time zone, 'yyyy'::text) || '00')::character varying
	WHEN am.is_opening_close = true AND to_char(am.date::timestamp with time zone, 'mmdd'::text) = '1231'::text THEN (to_char(am.date::timestamp with time zone, 'yyyy'::text) || '13')::character varying
	ELSE to_char(am.date::timestamp with time zone, 'yyyymm'::text)::character varying
END AS periodo,
b1.date as fecha,
aj.code as libro,
am.name AS voucher,
llit.code_sunat as td_partner,
rp.vat as doc_partner,
rp.name as partner,
lldt.code as td_sunat,
TRIM(b1.nro_comp)::character varying as nro_comprobante,
b3.fecha_emision AS fecha_doc,
b3.fecha_vencimiento AS fecha_ven,
aa.code as cuenta,
rc.name as moneda,
b1.debit as debe,
b1.credit as haber,
b1.balance,
b1.importe_me,
b1.saldo,
b1.saldo_me,
aml.partner_id,
b1.account_id from (
	WITH base_query AS (
    SELECT a2.date,
	       a1.id as move_line_id,
           a1.account_id,
           a1.partner_id,
           a1.type_document_id,
           TRIM(a1.nro_comp)::character varying AS nro_comp,
           a1.debit,
           a1.credit,
		   SUM(coalesce(a1.amount_currency,0)) OVER (PARTITION BY a1.account_id, a1.partner_id, a1.type_document_id, TRIM(a1.nro_comp))  AS saldo_me,
	       (coalesce(a1.debit,0) - coalesce(a1.credit,0)) as balance,
		   (coalesce(a1.amount_currency,0)) as importe_me,
           SUM(a1.debit) OVER (PARTITION BY a1.account_id, a1.partner_id, a1.type_document_id, TRIM(a1.nro_comp)) AS total_debit,
           SUM(a1.credit) OVER (PARTITION BY a1.account_id, a1.partner_id, a1.type_document_id, TRIM(a1.nro_comp)) AS total_credit
    FROM account_move_line a1
    LEFT JOIN account_move a2 ON a2.id = a1.move_id
    LEFT JOIN account_account a3 ON a3.id = a1.account_id
    LEFT JOIN account_account_type a4 ON a4.id = a3.user_type_id
    WHERE (a2.date BETWEEN date_from AND date_to)
      AND a2.state = 'posted'
      AND a3.is_document_an = TRUE
      AND a3.company_id = $3
	)
	SELECT date,
		bq.account_id,
		bq.partner_id,
		bq.type_document_id,
		bq.nro_comp,
		bq.debit,
		bq.credit,
		bq.balance,
		bq.importe_me,
		(bq.total_debit - bq.total_credit) AS saldo,
		bq.saldo_me,
		bq.move_line_id
	FROM base_query bq
	ORDER BY bq.account_id,
			bq.partner_id,
			bq.type_document_id,
			bq.nro_comp,
			bq.date
)b1
LEFT JOIN ctas_ctes($3) b3 on (b3.account_id=b1.account_id and b3.partner_id=b1.partner_id and b3.type_document_id=b1.type_document_id and TRIM(b3.nro_comp)=TRIM(b1.nro_comp))
LEFT JOIN account_move_line aml ON aml.id = b1.move_line_id
LEFT JOIN account_move am ON am.id = aml.move_id
LEFT JOIN account_journal aj ON aj.id = am.journal_id
LEFT JOIN account_account aa ON aa.id = b1.account_id
LEFT JOIN res_currency rc ON rc.id = aml.currency_id
LEFT JOIN res_partner rp ON rp.id = b1.partner_id
LEFT JOIN l10n_latam_identification_type llit ON llit.id = rp.l10n_latam_identification_type_id
LEFT JOIN l10n_latam_document_type lldt ON lldt.id = b1.type_document_id
order by aml.create_date desc,b1.partner_id, b1.account_id,lldt.code, b1.nro_comp;
END;
	$BODY$
	LANGUAGE plpgsql VOLATILE
	COST 100
	ROWS 1000;

---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
DROP FUNCTION IF EXISTS public.get_saldos_me_global(character varying,character varying,integer) CASCADE;

CREATE OR REPLACE FUNCTION public.get_saldos_me_global(
    periodo_apertura character varying,
    periodo character varying,
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
        --LEFT JOIN res_currency a4 on a4.id = a2.currency_id
        WHERE a2.currency_id is not null AND
        a2.dif_cambio_type = 'global' AND (a1.periodo::integer between $1::integer and $2::integer)
        GROUP BY a1.account_id;
END;
$BODY$;
-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
DROP FUNCTION IF EXISTS public.get_saldos_me_global_2(character varying,character varying,integer) CASCADE;

CREATE OR REPLACE FUNCTION public.get_saldos_me_global_2(
	periodo_apertura character varying,
	periodo character varying,
	company_id integer)
    RETURNS TABLE(account_id integer, debe numeric, haber numeric, saldomn numeric, saldome numeric, group_balance character varying, tc numeric) 
    LANGUAGE 'plpgsql'

    COST 100
    VOLATILE 
    ROWS 1000
AS $BODY$
BEGIN
	RETURN QUERY  
 SELECT
    b1.account_id,
    b1.debe,
    b1.haber,
    b1.saldomn,
    b1.saldome,
    b3.group_balance,
        CASE
            WHEN b3.group_balance::text = ANY (ARRAY['B1'::character varying, 'B2'::character varying]::text[]) THEN ( SELECT edcl.compra
               FROM exchange_diff_config_line edcl
                 LEFT JOIN exchange_diff_config edc ON edc.id = edcl.line_id
                 LEFT JOIN account_period ap ON ap.id = edcl.period_id
              WHERE edc.company_id = $3 AND ap.code::text = $2::text and edcl.currency_id = b2.currency_id)
            ELSE ( SELECT edcl.venta
               FROM exchange_diff_config_line edcl
                 LEFT JOIN exchange_diff_config edc ON edc.id = edcl.line_id
                 LEFT JOIN account_period ap ON ap.id = edcl.period_id
              WHERE edc.company_id = $3 AND ap.code::text = $2::text and edcl.currency_id = b2.currency_id)
        END AS tc
   FROM get_saldos_me_global($1,$2,$3) b1
     LEFT JOIN account_account b2 ON b2.id = b1.account_id
     LEFT JOIN account_type_it b3 ON b3.id = b2.account_type_it_id;
END;
$BODY$;

----------------------------------------------------------------------------------------------------------------------------------------------------------
DROP FUNCTION IF EXISTS public.get_saldos_me_global_final(character varying,character varying,integer) CASCADE;

CREATE OR REPLACE FUNCTION public.get_saldos_me_global_final(
	fiscal_year character varying,
	periodo character varying,
	company_id integer)
    RETURNS TABLE(account_id integer, debe numeric, haber numeric, saldomn numeric, saldome numeric, group_balance character varying, tc numeric, saldo_act numeric, diferencia numeric, difference_account_id integer) 
    LANGUAGE 'plpgsql'

    COST 100
    VOLATILE 
    ROWS 1000
AS $BODY$
BEGIN
	RETURN QUERY  
	SELECT *,
	round(coalesce(vst.tc,0) * vst.saldome,2) AS saldo_act,
	vst.saldomn - round(coalesce(vst.tc,0) * vst.saldome,2) AS diferencia,
	CASE 
	WHEN vst.saldomn < round(vst.tc * vst.saldome,2) AND vst.group_balance IN ('B1','B2') THEN (SELECT edc.profit_account_id FROM exchange_diff_config edc WHERE edc.company_id = $3)
	WHEN vst.saldomn > round(vst.tc * vst.saldome,2) AND vst.group_balance IN ('B1','B2') THEN (SELECT edc.loss_account_id FROM exchange_diff_config edc WHERE edc.company_id = $3)
	WHEN (-1 * vst.saldomn) > (-1 * round(vst.tc * vst.saldome,2)) AND vst.group_balance IN ('B3','B4','B5') THEN (SELECT edc.profit_account_id FROM exchange_diff_config edc WHERE edc.company_id = $3)
	WHEN (-1 * vst.saldomn) < (-1 * round(vst.tc * vst.saldome,2)) AND vst.group_balance IN ('B3','B4','B5') THEN (SELECT edc.loss_account_id FROM exchange_diff_config edc WHERE edc.company_id = $3) END AS difference_account_id
	FROM get_saldos_me_global_2($1||'00',$2,$3) vst;
END;
$BODY$;

----------------------------------------------------------------------------------------------------------------------------------------------------------
DROP FUNCTION IF EXISTS public.get_saldos_me_documento(character varying,character varying,integer) CASCADE;

CREATE OR REPLACE FUNCTION public.get_saldos_me_documento(
	periodo_apertura character varying,
	periodo character varying,
	company_id integer)
    RETURNS TABLE(partner_id integer, account_id integer, td_sunat character varying, nro_comprobante character varying, debe numeric, haber numeric, saldomn numeric, saldome numeric, type_document_id integer) 
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
	sum(coalesce(a1.importe_me,0)) as saldome,
	aml.type_document_id
	from get_diariog((select date_start from account_period where code = $1::character varying limit 1),(select date_end from account_period where code = $2::character varying  limit 1),$3) a1
	left join account_account a2 on a2.id=a1.account_id
	left join account_type_it a3 on a3.id=a2.account_type_it_id
	--left join res_currency a4 on a4.id = a2.currency_id
	left join account_move_line aml on aml.id = a1.move_line_id
	where 
	a2.dif_cambio_type = 'doc' and
	a2.currency_id is not null and
	(a1.periodo::int between $1::int and $2::int)
	group by a1.partner_id,a1.account_id,a1.td_sunat,a1.nro_comprobante, aml.type_document_id
	having (sum(a1.balance)+sum(a1.importe_me)) <> 0;
END;
$BODY$;

----------------------------------------------------------------------------------------------------------------------------------------------------------
DROP FUNCTION IF EXISTS public.get_saldos_me_documento_2(character varying,character varying,integer) CASCADE;

CREATE OR REPLACE FUNCTION public.get_saldos_me_documento_2(
	periodo_apertura character varying,
	periodo character varying,
	company_id integer)
    RETURNS TABLE(partner_id integer, account_id integer, td_sunat character varying, nro_comprobante character varying, debe numeric, haber numeric, saldomn numeric, saldome numeric, type_document_id integer, group_balance character varying, tc numeric) 
    LANGUAGE 'plpgsql'

    COST 100
    VOLATILE 
    ROWS 1000
AS $BODY$
BEGIN
	RETURN QUERY  
select b1.partner_id,
b1.account_id,
b1.td_sunat,
b1.nro_comprobante,
b1.debe,
b1.haber,
b1.saldomn,
b1.saldome,
b1.type_document_id,
b3.group_balance,
CASE
	WHEN b3.group_balance::text = ANY (ARRAY['B1'::character varying, 'B2'::character varying]::text[]) THEN ( SELECT edcl.compra
		FROM exchange_diff_config_line edcl
			LEFT JOIN exchange_diff_config edc ON edc.id = edcl.line_id
			LEFT JOIN account_period ap ON ap.id = edcl.period_id
		WHERE edc.company_id = $3 AND ap.code::text = $2::text and edcl.currency_id = b2.currency_id)
	ELSE ( SELECT edcl.venta
		FROM exchange_diff_config_line edcl
			LEFT JOIN exchange_diff_config edc ON edc.id = edcl.line_id
			LEFT JOIN account_period ap ON ap.id = edcl.period_id
		WHERE edc.company_id = $3 AND ap.code::text = $2::text and edcl.currency_id = b2.currency_id)
END AS tc
from get_saldos_me_documento($1,$2,$3) b1
LEFT JOIN account_account b2 ON b2.id = b1.account_id
LEFT JOIN account_type_it b3 ON b3.id = b2.account_type_it_id;
END;
$BODY$;

----------------------------------------------------------------------------------------------------------------------------------------------------------
DROP FUNCTION IF EXISTS public.get_saldos_me_documento_final(character varying,character varying,integer) CASCADE;

CREATE OR REPLACE FUNCTION public.get_saldos_me_documento_final(
	fiscal_year character varying,
	periodo character varying,
	company_id integer)
    RETURNS TABLE(partner_id integer, account_id integer, td_sunat character varying, nro_comprobante character varying, debe numeric, haber numeric, saldomn numeric, saldome numeric, type_document_id integer, group_balance character varying, tc numeric, saldo_act numeric, diferencia numeric, difference_account_id integer) 
    LANGUAGE 'plpgsql'

    COST 100
    VOLATILE 
    ROWS 1000
AS $BODY$
BEGIN
	RETURN QUERY  
	SELECT *,
	round(coalesce(vst.tc,0) * vst.saldome,2) AS saldo_act,
	vst.saldomn - round(coalesce(vst.tc,0) * vst.saldome,2) AS diferencia,
	CASE 
	WHEN vst.saldomn < round(vst.tc * vst.saldome,2) AND vst.group_balance IN ('B1','B2') THEN (SELECT edc.profit_account_id FROM exchange_diff_config edc WHERE edc.company_id = $3)
	WHEN vst.saldomn > round(vst.tc * vst.saldome,2) AND vst.group_balance IN ('B1','B2') THEN (SELECT edc.loss_account_id FROM exchange_diff_config edc WHERE edc.company_id = $3)
	WHEN (-1 * vst.saldomn) > (-1 * round(vst.tc * vst.saldome,2)) AND vst.group_balance IN ('B3','B4','B5') THEN (SELECT edc.profit_account_id FROM exchange_diff_config edc WHERE edc.company_id = $3)
	WHEN (-1 * vst.saldomn) < (-1 * round(vst.tc * vst.saldome,2)) AND vst.group_balance IN ('B3','B4','B5') THEN (SELECT edc.loss_account_id FROM exchange_diff_config edc WHERE edc.company_id = $3) END AS difference_account_id
	FROM get_saldos_me_documento_2($1||'00',$2,$3) vst;
END;
$BODY$;
-------------------------------------------------------------------------------------------------------------------------------------------------------------
DROP FUNCTION IF EXISTS public.get_maturity_analysis(date, date, integer, character varying) CASCADE;

CREATE OR REPLACE FUNCTION public.get_maturity_analysis(
	first_date date,
	end_date date,
	company_id integer,
	type character varying)
    RETURNS TABLE(fecha_emi date, fecha_ven date, cuenta character varying, divisa character varying, tdp character varying, doc_partner character varying, partner character varying, td_sunat character varying, nro_comprobante character varying, saldo_mn numeric, saldo_me numeric, partner_id integer, cero_treinta numeric, treinta1_sesenta numeric, sesenta1_noventa numeric, noventa1_ciento20 numeric, ciento21_ciento50 numeric, ciento51_ciento80 numeric, ciento81_mas numeric) 
    LANGUAGE 'plpgsql'

    COST 100
    VOLATILE 
    ROWS 1000
AS $BODY$
BEGIN
	RETURN QUERY  
	select 
	b1.fecha_emi,
	b1.fecha_ven,
	b1.cuenta,
	b1.divisa,
	b1.tdp,
	b1.doc_partner,
	b1.partner,
	b1.td_sunat,
	b1.nro_comprobante,
	b1.saldo_mn,
	b1.saldo_me,
	b1.partner_id,
	case when b1.atraso between 0 and 30 then b1.saldo_mn else 0 end as cero_treinta,
	case when b1.atraso between 31 and 60 then b1.saldo_mn else 0 end as treinta1_sesenta,
	case when b1.atraso between 61 and 90 then b1.saldo_mn else 0 end as sesenta1_noventa,
	case when b1.atraso between 91 and 120 then b1.saldo_mn else 0 end as noventa1_ciento20,
	case when b1.atraso between 121 and 150 then b1.saldo_mn else 0 end as ciento21_ciento50,
	case when b1.atraso between 151 and 180 then b1.saldo_mn else 0 end as ciento51_ciento80,
	case when b1.atraso >180 then b1.saldo_mn else 0 end as ciento81_mas 
	from
	(
	select 
	case when a1.fecha_doc::date is null then a1.fecha_con::date else a1.fecha_doc::date end as fecha_emi,
	a1.fecha_ven as fecha_ven,
	a1.cuenta as cuenta,
	case when a3.name is not null then a3.name else 'PEN' end as divisa,
	a1.td_partner as tdp,
	a1.doc_partner as doc_partner,
	a1.partner,
	a1.td_sunat,
	a1.nro_comprobante,
	case when  a2.internal_type='receivable' then a1.saldo_mn else -a1.saldo_mn end as saldo_mn,
	case when  a2.internal_type='receivable' then a1.saldo_me else -a1.saldo_me end as saldo_me,
	case when a1.fecha_ven is not null then $2 - a1.fecha_ven else 0 end as atraso,
	a1.account_id,
	a2.internal_type,
	a1.partner_id
	from 
	get_saldos($1,$2,$3) a1
	left join account_account a2 on a2.id=a1.account_id
	left join res_currency a3 on a3.id=a2.currency_id
	where a1.nro_comprobante is not null and a1.saldo_mn <> 0
	)b1
	where b1.internal_type = $4;
END;
$BODY$;