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

select a1.id as move_line_id, a1.move_id, a1.account_id,a1.partner_id,a1.type_document_id,a1.nro_comp,
a1.invoice_date_it as fecha_emision,
a1.date_maturity as fecha_vencimiento
from account_move_line a1
left join account_move a2 on a2.id=a1.move_id
left join account_account a3 on a3.id=a1.account_id
where a3.is_document_an=TRUE and a2.state='posted' and a1.company_id=$1 and a1.cta_cte_origen = TRUE;
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
(case when b2.fecha_contable is null then am.date else b2.fecha_contable end) AS fecha_con,
aj.code as libro,
am.name as voucher,
lit.code_sunat as td_partner,
rp.vat as doc_partner,
rp.name as partner,
ec1.code as td_sunat,
b1.nro_comp as nro_comprobante,
b3.fecha_emision as fecha_doc,
b3.fecha_vencimiento as fecha_ven,
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
)b2 on (b2.account_id=b1.account_id and b2.partner_id=b1.partner_id and b2.type_document_id=b1.type_document_id and b2.nro_comp=b1.nro_comp)

left join ctas_ctes($3) b3 on (b3.account_id=b1.account_id and b3.partner_id=b1.partner_id and b3.type_document_id=b1.type_document_id and b3.nro_comp=b1.nro_comp)
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
---update account_move_line set invoice_date_it = T.invoice_date, cta_cte_origen = True from (
---select aml.id, am.invoice_date from account_move_line aml
---left join account_move am on am.id = aml.move_id
---left join account_account aa on aa.id = aml.account_id
---where am.state = 'posted' and aa.internal_type in ('receivable','payable') and am.move_type <> 'entry')T
---where account_move_line.id = T.id