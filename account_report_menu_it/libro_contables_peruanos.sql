
CREATE OR REPLACE FUNCTION public.periodo_de_fecha(
date,boolean)
    RETURNS integer
    LANGUAGE 'sql'
    COST 100
    VOLATILE 
AS $BODY$
 
select 
case 
         when $2=true and lpad(extract(month from $1) :: VARCHAR,2,'0')='01' and lpad(extract(day from $1) :: VARCHAR,2,'0')='01' then 
         concat(extract(year from $1),'00')::integer 
         when $2=true and lpad(extract(month from $1) :: VARCHAR,2,'0')='12' and lpad(extract(day from $1) :: VARCHAR,2,'0')='31' then 
         concat(extract(year from $1),'13')::integer
else
         concat(extract(year from $1),lpad(extract(month from $1) :: VARCHAR,2,'0')):: integer  end as periodo
 
$BODY$;
------------------------------------------------------------------------------------------------
DROP FUNCTION IF EXISTS public.get_diariog(date, date, integer) CASCADE;

CREATE OR REPLACE FUNCTION public.get_diariog(
	date_from date,
	date_to date,
	company_id integer)
	RETURNS TABLE(periodo integer, fecha date, libro character varying, voucher character varying, cuenta character varying, debe numeric, haber numeric, balance numeric, moneda character varying, 
	tc numeric, importe_me numeric, cta_analitica character varying, glosa character varying, td_partner character varying, doc_partner character varying, partner character varying, td_sunat character varying, 
	nro_comprobante character varying, fecha_doc date, fecha_ven date, col_reg character varying, monto_reg numeric, medio_pago character varying, ple_diario character varying, ple_compras character varying,
	ple_ventas character varying, move_id integer, move_line_id integer, account_id integer, analytic_account_id integer, partner_id integer) AS
	$BODY$
	BEGIN
	RETURN QUERY 
	SELECT
	CASE
		WHEN a1.is_opening_close = true AND to_char(a1.date::timestamp with time zone, 'mmdd'::text) = '0101'::text THEN (to_char(a1.date::timestamp with time zone, 'yyyy'::text) || '00')::integer
		WHEN a1.is_opening_close = true AND to_char(a1.date::timestamp with time zone, 'mmdd'::text) = '1231'::text THEN (to_char(a1.date::timestamp with time zone, 'yyyy'::text) || '13')::integer
		ELSE to_char(a1.date::timestamp with time zone, 'yyyymm'::text)::integer
	END AS periodo,
	a1.date AS fecha,
	a3.code AS libro,
	a1.name AS voucher,
	a4.code AS cuenta,
	a2.debit AS debe,
	a2.credit AS haber,
	a2.balance,
	CASE
		WHEN a2.currency_id IS NULL THEN 'PEN'::character varying
		ELSE a5.name
	END AS moneda,
	coalesce(case when a2.tc = 0 then  1 else a2.tc end,1) as tc,
	case when a2.currency_id IS NULL OR a5.name = 'PEN' THEN 0 ELSE a2.amount_currency END AS importe_me,
	a11.code AS cta_analitica,
	a1.glosa,
	a7.code_sunat AS td_partner,
	a6.vat AS doc_partner,
	a6.name AS partner,
	a8.code AS td_sunat,
	REPLACE(a2.nro_comp,'/','-')::character varying AS nro_comprobante,
	a1.invoice_date AS fecha_doc,
	a2.date_maturity AS fecha_ven,
	a10.name AS col_reg,
	a2.tax_amount_it AS monto_reg,
	a12.code AS medio_pago,
	a1.ple_state AS ple_diario,
	a1.campo_41_purchase AS ple_compras,
	a1.campo_34_sale AS ple_ventas,
	a1.id AS move_id,
	a2.id AS move_line_id,
	a2.account_id,
	a2.analytic_account_id,
	a2.partner_id
	FROM account_move a1
		LEFT JOIN account_move_line a2 ON a2.move_id = a1.id
		LEFT JOIN account_journal a3 ON a3.id = a1.journal_id
		LEFT JOIN account_account a4 ON a4.id = a2.account_id
		LEFT JOIN res_currency a5 ON a5.id = a2.currency_id
		LEFT JOIN res_partner a6 ON a6.id = a2.partner_id
		LEFT JOIN l10n_latam_identification_type a7 ON a7.id = a6.l10n_latam_identification_type_id
		LEFT JOIN l10n_latam_document_type a8 ON a8.id = a2.type_document_id
		LEFT JOIN account_account_tag_account_move_line_rel a9 ON a9.account_move_line_id = a2.id
		LEFT JOIN account_account_tag a10 ON a10.id = a9.account_account_tag_id
		LEFT JOIN account_analytic_account a11 ON a11.id = a2.analytic_account_id
		LEFT JOIN einvoice_catalog_payment a12 ON a12.id = a1.td_payment_id
	WHERE a1.state::text = 'posted'::text AND a2.display_type IS NULL AND a2.account_id IS NOT NULL AND (a1.date::date BETWEEN $1 and $2) AND a1.company_id = $3
	ORDER BY (date_part('month'::text, a1.date)), a3.code, a1.name, a2.debit DESC, a4.code;
	END;
	$BODY$
	LANGUAGE plpgsql VOLATILE
	COST 100
	ROWS 1000;
--------------------------------------------------------------------------------------------------------------------------

DROP FUNCTION IF EXISTS public.get_mayorg(date, date, integer,integer[]) CASCADE;

CREATE OR REPLACE FUNCTION public.get_mayorg(
	date_from date,
	date_to date,
	company_id integer,
  account_ids integer[])
	RETURNS TABLE(periodo integer, fecha date, libro character varying, voucher character varying, cuenta character varying, debe numeric, 
	debe_me numeric, haber numeric, haber_me numeric, balance numeric, balance_me numeric, saldo numeric, saldo_me numeric, moneda character varying, 
	tc numeric, cta_analitica character varying, glosa character varying, td_partner character varying, doc_partner character varying, partner character varying, td_sunat character varying, 
	nro_comprobante character varying, fecha_doc date, fecha_ven date, account_id integer, move_id integer, move_line_id integer) AS
	$BODY$
	BEGIN
	RETURN QUERY 
select 
CASE
	WHEN am.is_opening_close = true AND to_char(am.date::timestamp with time zone, 'mmdd'::text) = '0101'::text THEN (to_char(am.date::timestamp with time zone, 'yyyy'::text) || '00')::integer
	WHEN am.is_opening_close = true AND to_char(am.date::timestamp with time zone, 'mmdd'::text) = '1231'::text THEN (to_char(am.date::timestamp with time zone, 'yyyy'::text) || '13')::integer
	ELSE to_char(am.date::timestamp with time zone, 'yyyymm'::text)::integer
END AS periodo,
T.fecha,
aj.code as libro,
am.name AS voucher,
aa.code as cuenta,
T.debit as debe,
T.debit_me as debe_me,
T.credit as haber,
T.credit_me as haber_me,
T.balance,
T.balance_me,
sum(coalesce(T.balance,0)) OVER (partition by T.account_id order by T.account_id,T.fecha,T.move_line_id) as saldo,
sum(coalesce(T.balance_me,0)) OVER (partition by T.account_id order by T.account_id,T.fecha,T.move_line_id) as saldo_me,
rc.name as moneda,
aml.tc,
ana.name as cta_analitica,
am.glosa,
llit.code_sunat as td_partner,
rp.vat as doc_partner,
rp.name as partner,
lldt.code as td_sunat,
aml.nro_comp as nro_comprobante,
am.invoice_date AS fecha_doc,
aml.date_maturity AS fecha_ven,
T.account_id,
T.move_id,
T.move_line_id from (
select
null as move_id,
0 as move_line_id,
date_from as fecha, 
aml.account_id,
sum(aml.debit) as debit,
case when sum(coalesce(aml.amount_currency,0)) > 0 then sum(coalesce(aml.amount_currency,0)) else 0 end as debit_me,
sum(aml.credit) as credit,
case when sum(coalesce(aml.amount_currency,0)) < 0 then abs(sum(coalesce(aml.amount_currency,0))) else 0 end as credit_me,
sum(coalesce(aml.balance)) as balance,
sum(coalesce(aml.amount_currency,0)) as balance_me
from account_move_line aml
left join account_move am on am.id=aml.move_id
where (am.date between (EXTRACT (YEAR FROM date_from)::character varying ||'/01/01')::date and date_from - 1)   
and  am.state='posted'
and aml.display_type is null
and aml.account_id = ANY($4)
and am.company_id=$3
group by aml.account_id 
union all
select 
am.id as move_id,
aml.id as move_line_id,
am.date as fecha,
aml.account_id,
aml.debit,
case when aml.amount_currency > 0 then aml.amount_currency else 0 end as debit_me,
aml.credit,
case when aml.amount_currency < 0 then abs(aml.amount_currency) else 0 end as credit_me,
coalesce(aml.balance,0) as balance,
aml.amount_currency as balance_me
from account_move_line aml
left join account_move am on am.id=aml.move_id
where (am.date between date_from and date_to)
and  am.state='posted'
and aml.display_type is null
and aml.account_id = ANY($4)
and am.company_id=$3
)T
LEFT JOIN account_move_line aml ON T.move_line_id = aml.id
LEFT JOIN account_move am ON T.move_id = am.id
LEFT JOIN account_journal aj ON aj.id = am.journal_id
LEFT JOIN account_account aa ON aa.id = T.account_id
LEFT JOIN res_currency rc ON rc.id = aml.currency_id
LEFT JOIN account_analytic_account ana ON ana.id = aml.analytic_account_id
LEFT JOIN res_partner rp ON rp.id = aml.partner_id
LEFT JOIN l10n_latam_identification_type llit ON llit.id = rp.l10n_latam_identification_type_id
LEFT JOIN l10n_latam_document_type lldt ON lldt.id = aml.type_document_id
order by T.account_id,T.fecha,T.move_line_id;
END;
	$BODY$
	LANGUAGE plpgsql VOLATILE
	COST 100
	ROWS 1000;

---------Con esta vista se obtiene la primera linea de los documentos relacionados, sirve para el reporte de 
---------registro de ventas, compras.

CREATE OR REPLACE VIEW public.doc_rela_pri AS 
 SELECT doc_invoice_relac.move_id,
	min(doc_invoice_relac.id) AS min
   FROM doc_invoice_relac
  GROUP BY doc_invoice_relac.move_id;

--------------------------------------------------------------------------------------------------------------------------
DROP FUNCTION IF EXISTS public.get_ventas_1(date, date, integer) CASCADE;

CREATE OR REPLACE FUNCTION public.get_ventas_1(
	date_from date,
	date_to date,
	company_id integer)
	RETURNS TABLE(move_id integer, exp numeric, exp_me numeric, venta_g numeric, venta_g_me numeric, inaf numeric, inaf_me numeric, 
	exo numeric, exo_me numeric, isc_v numeric, isc_v_me numeric, otros_v numeric, otros_v_me numeric, igv_v numeric, igv_v_me numeric, 
	icbper numeric, icbper_me numeric) AS
	$BODY$
	BEGIN
	RETURN QUERY 
	SELECT am.id as move_id,
	sum(
		CASE
			WHEN aat.record_sale::text = '1'::text THEN - aml.tax_amount_it
			ELSE 0::numeric
		END) AS exp,
	sum(
		CASE
			WHEN aat.record_sale::text = '1'::text THEN - aml.tax_amount_me
			ELSE 0::numeric
		END) AS exp_me,
	sum(
		CASE
			WHEN aat.record_sale::text = '2'::text THEN - aml.tax_amount_it
			ELSE 0::numeric
		END) AS venta_g,
	sum(
		CASE
			WHEN aat.record_sale::text = '2'::text THEN - aml.tax_amount_me
			ELSE 0::numeric
		END) AS venta_g_me,
	sum(
		CASE
			WHEN aat.record_sale::text = '3'::text THEN - aml.tax_amount_it
			ELSE 0::numeric
		END) AS inaf,
	sum(
		CASE
			WHEN aat.record_sale::text = '3'::text THEN - aml.tax_amount_me
			ELSE 0::numeric
		END) AS inaf_me,
	sum(
		CASE
			WHEN aat.record_sale::text = '4'::text THEN - aml.tax_amount_it
			ELSE 0::numeric
		END) AS exo,
	sum(
		CASE
			WHEN aat.record_sale::text = '4'::text THEN - aml.tax_amount_me
			ELSE 0::numeric
		END) AS exo_me,
	sum(
		CASE
			WHEN aat.record_sale::text = '5'::text THEN - aml.tax_amount_it
			ELSE 0::numeric
		END) AS isc_v,
	sum(
		CASE
			WHEN aat.record_sale::text = '5'::text THEN - aml.tax_amount_me
			ELSE 0::numeric
		END) AS isc_v_me,
	sum(
		CASE
			WHEN aat.record_sale::text = '6'::text THEN - aml.tax_amount_it
			ELSE 0::numeric
		END) AS otros_v,
	sum(
		CASE
			WHEN aat.record_sale::text = '6'::text THEN - aml.tax_amount_me
			ELSE 0::numeric
		END) AS otros_v_me,
	sum(
		CASE
			WHEN aat.record_sale::text = '7'::text THEN - aml.tax_amount_it
			ELSE 0::numeric
		END) AS igv_v,
	sum(
		CASE
			WHEN aat.record_sale::text = '7'::text THEN - aml.tax_amount_me
			ELSE 0::numeric
		END) AS igv_v_me,
	sum(
		CASE
			WHEN aat.record_sale::text = '8'::text THEN - aml.tax_amount_it
			ELSE 0::numeric
		END) AS icbper,
	sum(
		CASE
			WHEN aat.record_sale::text = '8'::text THEN - aml.tax_amount_me
			ELSE 0::numeric
		END) AS icbper_me
	FROM account_move_line aml
	LEFT JOIN account_account_tag_account_move_line_rel rel ON rel.account_move_line_id = aml.id
	LEFT JOIN account_account_tag aat ON aat.id = rel.account_account_tag_id
	LEFT JOIN account_move am on am.id = aml.move_id
	LEFT JOIN account_journal aj on aj.id = am.journal_id
	WHERE am.state::text = 'posted'::text AND aml.display_type IS NULL AND aml.account_id IS NOT NULL AND (am.date::date BETWEEN $1 and $2) AND am.company_id = $3
	AND aj.register_sunat = '2' AND rel.account_account_tag_id IS NOT NULL
	GROUP BY am.id;
END;
	$BODY$
	LANGUAGE plpgsql VOLATILE
	COST 100
	ROWS 1000;
--------------------------------------------------------------------------------------------------------------------------
DROP FUNCTION IF EXISTS public.get_ventas_1_1(date, date, integer, character varying) CASCADE;

CREATE OR REPLACE FUNCTION public.get_ventas_1_1(
	date_from date,
	date_to date,
	company_id integer,
	currency character varying)
RETURNS TABLE(periodo integer, fecha_cont date,libro character varying, voucher character varying, fecha_e date, fecha_v date,
	td character varying, serie character varying, anio character varying, numero character varying, tdp character varying, docp character varying,
	namep character varying, exp numeric, venta_g numeric, inaf numeric, exo numeric, isc_v numeric, otros_v numeric, igv_v numeric, icbper numeric,
	total numeric, name character varying, monto_me numeric, currency_rate numeric, fecha_det date, comp_det character varying, f_doc_m date,
	td_doc_m character varying, serie_m character varying, numero_m character varying, glosa character varying, estado_ple character varying, am_id integer) AS
	$BODY$
	BEGIN
	RETURN QUERY 
	SELECT CASE
		WHEN am.is_opening_close = true AND to_char(am.date::timestamp with time zone, 'mmdd'::text) = '0101'::text THEN (to_char(am.date::timestamp with time zone, 'yyyy'::text) || '00')::integer
		WHEN am.is_opening_close = true AND to_char(am.date::timestamp with time zone, 'mmdd'::text) = '1231'::text THEN (to_char(am.date::timestamp with time zone, 'yyyy'::text) || '13')::integer
		ELSE to_char(am.date::timestamp with time zone, 'yyyymm'::text)::integer
		END AS periodo,
			am.date AS fecha_cont,
			aj.code AS libro,
			am.name AS voucher,
			am.invoice_date AS fecha_e,
			am.invoice_date_due AS fecha_v,
			ec1.code AS td,
			CASE
				WHEN split_part(am.ref, '-', 2) <> '' THEN split_part(am.ref, '-', 1)::character varying
				ELSE ''
			END
			AS serie,
			CASE
				WHEN ec1.code = '50' THEN to_char(am.invoice_date , 'yyyy')::character varying
				ELSE NULL
			END AS anio,
			CASE
				WHEN split_part(am.ref, '-', 2) <> '' THEN split_part(am.ref, '-', 2)::character varying
				ELSE split_part(am.ref, '-', 1)::character varying
			END
			AS numero,
			lit.code_sunat AS tdp,
			rp.vat AS docp,
			rp.name AS namep,
			case when $4 = 'pen' then coalesce(mv.exp,0) else coalesce(mv.exp_me,0) end as exp,
			case when $4 = 'pen' then coalesce(mv.venta_g,0) else coalesce(mv.venta_g_me,0) end as venta_g,
			case when $4 = 'pen' then coalesce(mv.inaf,0) else coalesce(mv.inaf_me,0) end as inaf,
			case when $4 = 'pen' then coalesce(mv.exo,0) else coalesce(mv.exo_me,0) end as exo,
			case when $4 = 'pen' then coalesce(mv.isc_v,0) else coalesce(mv.isc_v_me,0) end as isc_v,
			case when $4 = 'pen' then coalesce(mv.otros_v,0) else coalesce(mv.otros_v_me,0) end as otros_v,
			case when $4 = 'pen' then coalesce(mv.igv_v,0) else coalesce(mv.igv_v_me,0) end as igv_v,
			case when $4 = 'pen' then coalesce(mv.icbper,0) else coalesce(mv.icbper_me,0) end as icbper,
			case when $4 = 'pen' then 
			(coalesce(mv.exp,0) + coalesce(mv.venta_g,0) + coalesce(mv.inaf,0) + coalesce(mv.exo,0) + coalesce(mv.isc_v,0) + 
			coalesce(mv.otros_v,0) + coalesce(mv.igv_v,0) + coalesce(mv.icbper,0)) 
			else (coalesce(mv.exp_me,0) + coalesce(mv.venta_g_me,0) + coalesce(mv.inaf_me,0) + coalesce(mv.exo_me,0) + coalesce(mv.isc_v_me,0) + 
			coalesce(mv.otros_v_me,0) + coalesce(mv.igv_v_me,0) + coalesce(mv.icbper_me,0)) end AS total,
			rc.name,
			(coalesce(mv.exp_me,0) + coalesce(mv.venta_g_me,0) + coalesce(mv.inaf_me,0) + coalesce(mv.exo_me,0) + coalesce(mv.isc_v_me,0) + 
			coalesce(mv.otros_v_me,0) + coalesce(mv.igv_v_me,0) + coalesce(mv.icbper_me,0)) AS monto_me,
			case when rc.name = 'PEN' then 1 else am.currency_rate end as currency_rate,
			am.date_detraccion AS fecha_det,
			am.voucher_number AS comp_det,
			dr.date AS f_doc_m,
			eic1.code AS td_doc_m,
			CASE
				WHEN split_part(dr.nro_comprobante, '-', 2) <> '' THEN split_part(dr.nro_comprobante, '-', 1)::character varying
				ELSE null
			END
			AS serie_m,
			CASE
				WHEN split_part(dr.nro_comprobante, '-', 2) <> '' THEN split_part(dr.nro_comprobante, '-', 2)::character varying
				ELSE split_part(dr.nro_comprobante, '-', 1)::character varying
			END
			AS numero_m,
			am.glosa,
			am.campo_34_sale AS estado_ple,
			am.id::integer as am_id
		   FROM account_move am
			 LEFT JOIN account_journal aj ON aj.id = am.journal_id
			 LEFT JOIN res_partner rp ON rp.id = am.partner_id
			 LEFT JOIN l10n_latam_identification_type lit ON lit.id = rp.l10n_latam_identification_type_id
			 LEFT JOIN l10n_latam_document_type ec1 ON ec1.id = am.l10n_latam_document_type_id
			 LEFT JOIN ( SELECT a2.type_document_id,
					a2.date,
					a2.nro_comprobante,
					a2.amount_currency,
					a2.amount,
					a2.bas_amount,
					a2.tax_amount,
					a2.id,
					a2.move_id
				   FROM doc_rela_pri a1
					 LEFT JOIN doc_invoice_relac a2 ON a1.min = a2.id) dr ON dr.move_id = am.id
			 LEFT JOIN l10n_latam_document_type eic1 ON eic1.id = dr.type_document_id
			 LEFT JOIN get_ventas_1($1,$2,$3) mv ON mv.move_id = am.id
			 LEFT JOIN res_currency rc ON rc.id = am.currency_id
		  WHERE aj.register_sunat::text = '2'::text AND am.state::text = 'posted'::text
		  AND (am.date::date BETWEEN $1 and $2) AND am.company_id = $3
		  ORDER BY ("left"(to_char(am.date::timestamp with time zone, 'yyyymmdd'::text), 6)), aj.code, am.name;
END;
	$BODY$
	LANGUAGE plpgsql VOLATILE
	COST 100
	ROWS 1000;
--------------------------------------------------------------------------------------------------------------------------
DROP FUNCTION IF EXISTS public.get_ventas_2_bm(date, date, integer) CASCADE;

CREATE OR REPLACE FUNCTION public.get_ventas_2_bm(
	date_from date,
	date_to date,
	company_id integer)
	RETURNS TABLE(move_id integer, cod_destino integer, ventag numeric, ventang numeric, isc numeric, igv numeric, icbper numeric, otros numeric) AS
	$BODY$
	BEGIN
	RETURN QUERY 
	SELECT a1.move_id,
        CASE
            WHEN (
            CASE
                WHEN a1.venta_g <> 0::numeric THEN '1'::text
                ELSE '0'::text
            END ||
            CASE
                WHEN (a1.exp + a1.exo + a1.inaf) <> 0::numeric THEN '1'::text
                ELSE '0'::text
            END) = '10'::text THEN 1
            WHEN (
            CASE
                WHEN a1.venta_g <> 0::numeric THEN '1'::text
                ELSE '0'::text
            END ||
            CASE
                WHEN (a1.exp + a1.exo + a1.inaf) <> 0::numeric THEN '1'::text
                ELSE '0'::text
            END) = '01'::text THEN 2
            ELSE 3
        END AS cod_destino,
        CASE
            WHEN a3.name::text = 'PEN'::text THEN a1.venta_g
            ELSE a1.venta_g_me
        END AS ventag,
        CASE
            WHEN a3.name::text = 'PEN'::text THEN a1.exp + a1.exo + a1.inaf
            ELSE a1.exp_me + a1.exo_me + a1.inaf_me
        END AS ventang,
        CASE
            WHEN a3.name::text = 'PEN'::text THEN a1.isc_v
            ELSE a1.isc_v_me
        END AS isc,
        CASE
            WHEN a3.name::text = 'PEN'::text THEN a1.igv_v
            ELSE a1.igv_v_me
        END AS igv,
         CASE
            WHEN a3.name::text = 'PEN'::text THEN a1.icbper
            ELSE a1.icbper_me
        END AS icbper,
        CASE
            WHEN a3.name::text = 'PEN'::text THEN a1.otros_v
            ELSE a1.otros_v_me
        END AS otros
   FROM get_ventas_1($1,$2,$3) a1
     LEFT JOIN account_move a2 ON a2.id = a1.move_id
     LEFT JOIN res_currency a3 ON a3.id = a2.currency_id
  ORDER BY a1.move_id;
	END;
	$BODY$
	LANGUAGE plpgsql VOLATILE
	COST 100
	ROWS 1000;
--------------------------------------------------------------------------------------------------------------------------
DROP FUNCTION IF EXISTS public.get_pdb_ventas_1(date, date, integer) CASCADE;

CREATE OR REPLACE FUNCTION public.get_pdb_ventas_1(
	date_from date,
	date_to date,
	company_id integer)
	RETURNS TABLE(move_id integer, cod_destino integer, nro_destino integer, base numeric, isc numeric, igv numeric, otros numeric) AS
	$BODY$
	BEGIN
	RETURN QUERY 
	(SELECT bm.move_id,
		bm.cod_destino,
		1 AS nro_destino,
		bm.ventag AS base,
		bm.isc,
		bm.igv,
		bm.otros
	FROM get_ventas_2_bm($1,$2,$3) bm
	WHERE bm.ventag <> 0::numeric)
	UNION ALL
	(SELECT bm.move_id,
		bm.cod_destino,
		2 AS nro_destino,
		bm.ventang AS base,
		bm.isc,
		bm.igv,
		bm.otros
	FROM get_ventas_2_bm($1,$2,$3) bm
	WHERE bm.ventang <> 0::numeric)
	ORDER BY 1;
	END;
	$BODY$
	LANGUAGE plpgsql VOLATILE
	COST 100
	ROWS 1000;
--------------------------------------------------------------------------------------------------------------------------
DROP FUNCTION IF EXISTS public.get_pdb_ventas_2(date, date, integer) CASCADE;

CREATE OR REPLACE FUNCTION public.get_pdb_ventas_2(
	date_from date,
	date_to date,
	company_id integer)
	RETURNS TABLE(move_id integer, cod_destino integer, nro_destino integer, base numeric, isc numeric, igv numeric, otros numeric) AS
	$BODY$
	BEGIN
	RETURN QUERY 

	SELECT bm2.move_id,
    bm2.cod_destino,
        CASE
            WHEN bm2.cod_destino <> 3 THEN 1
            ELSE bm2.nro_destino
        END AS nro_destino,
    bm2.base,
        CASE
            WHEN min(bm2.nro_destino) OVER (PARTITION BY bm2.move_id) = bm2.nro_destino THEN bm2.isc
            ELSE 0::numeric
        END AS isc,
        CASE
            WHEN min(bm2.nro_destino) OVER (PARTITION BY bm2.move_id) = bm2.nro_destino THEN bm2.igv
            ELSE 0::numeric
        END AS igv,
        CASE
            WHEN min(bm2.nro_destino) OVER (PARTITION BY bm2.move_id) = bm2.nro_destino THEN bm2.otros
            ELSE 0::numeric
        END AS otros
   FROM get_pdb_ventas_1($1,$2,$3) bm2
  ORDER BY bm2.move_id, (
        CASE
            WHEN bm2.cod_destino <> 3 THEN 1
            ELSE bm2.nro_destino
        END);
	END;
	$BODY$
	LANGUAGE plpgsql VOLATILE
	COST 100
	ROWS 1000;
--------------------------------------------------------------------------------------------------------------------------
DROP FUNCTION IF EXISTS public.get_compras_1(date, date, integer) CASCADE;

CREATE OR REPLACE FUNCTION public.get_compras_1(
	date_from date,
	date_to date,
	company_id integer)
	RETURNS TABLE(move_id integer, base1 numeric, base1_me numeric, base2 numeric, base2_me numeric, base3 numeric, base3_me numeric, cng numeric, cng_me numeric, 
	isc numeric, isc_me numeric, otros numeric, otros_me numeric, igv1 numeric, igv1_me numeric, igv2 numeric, igv2_me numeric, igv3 numeric, igv3_me numeric, 
	icbper numeric, icbper_me numeric) AS
	$BODY$
	BEGIN
	RETURN QUERY 
SELECT am.id as move_id,
	sum(
		CASE
			WHEN aat.record_shop::text = '1'::text THEN aml.tax_amount_it
			ELSE 0::numeric
		END) AS base1,
	sum(
		CASE
			WHEN aat.record_shop::text = '1'::text THEN aml.tax_amount_me
			ELSE 0::numeric
		END) AS base1_me,
	sum(
		CASE
			WHEN aat.record_shop::text = '2'::text THEN aml.tax_amount_it
			ELSE 0::numeric
		END) AS base2,
	sum(
		CASE
			WHEN aat.record_shop::text = '2'::text THEN aml.tax_amount_me
			ELSE 0::numeric
		END) AS base2_me,
	sum(
		CASE
			WHEN aat.record_shop::text = '3'::text THEN aml.tax_amount_it
			ELSE 0::numeric
		END) AS base3,
	
	sum(
		CASE
			WHEN aat.record_shop::text = '3'::text THEN aml.tax_amount_me
			ELSE 0::numeric
		END) AS base3_me,
	sum(
		CASE
			WHEN aat.record_shop::text = '4'::text THEN aml.tax_amount_it
			ELSE 0::numeric
		END) AS cng,
	sum(
		CASE
			WHEN aat.record_shop::text = '4'::text THEN aml.tax_amount_me
			ELSE 0::numeric
		END) AS cng_me,
	sum(
		CASE
			WHEN aat.record_shop::text = '5'::text THEN aml.tax_amount_it
			ELSE 0::numeric
		END) AS isc,
	sum(
		CASE
			WHEN aat.record_shop::text = '5'::text THEN aml.tax_amount_me
			ELSE 0::numeric
		END) AS isc_me,
	sum(
		CASE
			WHEN aat.record_shop::text = '6'::text THEN aml.tax_amount_it
			ELSE 0::numeric
		END) AS otros,
	sum(
		CASE
			WHEN aat.record_shop::text = '6'::text THEN aml.tax_amount_me
			ELSE 0::numeric
		END) AS otros_me,
	sum(
		CASE
			WHEN aat.record_shop::text = '7'::text THEN aml.tax_amount_it
			ELSE 0::numeric
		END) AS igv1,
	sum(
		CASE
			WHEN aat.record_shop::text = '7'::text THEN aml.tax_amount_me
			ELSE 0::numeric
		END) AS igv1_me,
	sum(
		CASE
			WHEN aat.record_shop::text = '8'::text THEN aml.tax_amount_it
			ELSE 0::numeric
		END) AS igv2,
	sum(
		CASE
			WHEN aat.record_shop::text = '8'::text THEN aml.tax_amount_me
			ELSE 0::numeric
		END) AS igv2_me,
	sum(
		CASE
			WHEN aat.record_shop::text = '9'::text THEN aml.tax_amount_it
			ELSE 0::numeric
		END) AS igv3,
	sum(
		CASE
			WHEN aat.record_shop::text = '9'::text THEN aml.tax_amount_me
			ELSE 0::numeric
		END) AS igv3_me,
	sum(
		CASE
			WHEN aat.record_shop::text = '10'::text THEN aml.tax_amount_it
			ELSE 0::numeric
		END) AS icbper,
	sum(
		CASE
			WHEN aat.record_shop::text = '10'::text THEN aml.tax_amount_me
			ELSE 0::numeric
		END) AS icbper_me
	from account_move_line aml
	LEFT JOIN account_account_tag_account_move_line_rel rel ON rel.account_move_line_id = aml.id
	LEFT JOIN account_account_tag aat ON aat.id = rel.account_account_tag_id
	LEFT JOIN account_move am on am.id = aml.move_id
	LEFT JOIN account_journal aj on aj.id = am.journal_id
	WHERE am.state::text = 'posted'::text AND aml.display_type IS NULL AND aml.account_id IS NOT NULL AND (am.date::date BETWEEN $1 and $2) AND am.company_id = $3
	AND aj.register_sunat = '1' AND rel.account_account_tag_id IS NOT NULL
	GROUP BY am.id;
END;
	$BODY$
	LANGUAGE plpgsql VOLATILE
	COST 100
	ROWS 1000;
--------------------------------------------------------------------------------------------------------------------------
DROP FUNCTION IF EXISTS public.get_compras_1_1(date, date, integer,character varying) CASCADE;

CREATE OR REPLACE FUNCTION public.get_compras_1_1(
	date_from date,
	date_to date,
	company_id integer,
	currency character varying)
RETURNS TABLE(periodo integer, fecha_cont date,libro character varying, voucher character varying, fecha_e date, fecha_v date,
	td character varying, serie character varying, anio character varying, numero character varying, tdp character varying, docp character varying,
	namep character varying, base1 numeric, base2 numeric, base3 numeric, cng numeric, isc numeric, otros numeric, igv1 numeric, igv2 numeric,
	igv3 numeric, icbper numeric, total numeric, name character varying, monto_me numeric, currency_rate numeric, fecha_det date, comp_det character varying, 
	f_doc_m date, td_doc_m character varying, serie_m character varying, numero_m character varying, glosa character varying, am_id integer, partner_id integer) AS
	$BODY$
	BEGIN
	RETURN QUERY 
	SELECT CASE
		WHEN am.is_opening_close = true AND to_char(am.date::timestamp with time zone, 'mmdd'::text) = '0101'::text THEN (to_char(am.date::timestamp with time zone, 'yyyy'::text) || '00')::integer
		WHEN am.is_opening_close = true AND to_char(am.date::timestamp with time zone, 'mmdd'::text) = '1231'::text THEN (to_char(am.date::timestamp with time zone, 'yyyy'::text) || '13')::integer
		ELSE to_char(am.date::timestamp with time zone, 'yyyymm'::text)::integer
		END AS periodo,
			am.date AS fecha_cont,
			aj.code AS libro,
			am.name AS voucher,
			am.invoice_date AS fecha_e,
			am.invoice_date_due AS fecha_v,
			ec1.code AS td,
			CASE
				WHEN split_part(am.ref, '-', 2) <> '' THEN split_part(am.ref, '-', 1)::character varying
				ELSE NULL
			END
			AS serie,
			CASE
				WHEN ec1.code in ('50','52') THEN to_char(am.invoice_date , 'yyyy')::character varying
				ELSE NULL
			END AS anio,
			CASE
				WHEN split_part(am.ref, '-', 2) <> '' THEN split_part(am.ref, '-', 2)::character varying
				ELSE split_part(am.ref, '-', 1)::character varying
			END
			AS numero,
			lit.code_sunat AS tdp,
			rp.vat AS docp,
			rp.name AS namep,
			case when $4 = 'pen' then coalesce(mc.base1,0) else coalesce(mc.base1_me,0) end as base1,
			case when $4 = 'pen' then coalesce(mc.base2,0) else coalesce(mc.base2_me,0) end as base2,
			case when $4 = 'pen' then coalesce(mc.base3,0) else coalesce(mc.base3_me,0) end as base3,
			case when $4 = 'pen' then coalesce(mc.cng,0) else coalesce(mc.cng_me,0) end as cng,
			case when $4 = 'pen' then coalesce(mc.isc,0) else coalesce(mc.isc_me,0) end as isc,
			case when $4 = 'pen' then coalesce(mc.otros,0) else coalesce(mc.otros_me,0) end as otros,
			case when $4 = 'pen' then coalesce(mc.igv1,0) else coalesce(mc.igv1_me,0) end as igv1,
			case when $4 = 'pen' then coalesce(mc.igv2,0) else coalesce(mc.igv2_me,0) end as igv2,
			case when $4 = 'pen' then coalesce(mc.igv3,0) else coalesce(mc.igv3_me,0) end as igv3,
			case when $4 = 'pen' then coalesce(mc.icbper,0) else coalesce(mc.icbper_me,0) end as icbper,
			case when $4 = 'pen' then 
			coalesce(mc.base1,0) + coalesce(mc.base2,0) + coalesce(mc.base3,0) + coalesce(mc.cng,0) + coalesce(mc.isc,0) + coalesce(mc.otros,0) + 
			coalesce(mc.igv1,0) + coalesce(mc.igv2,0) + coalesce(mc.igv3,0) + coalesce(mc.icbper,0)
			else coalesce(mc.base1_me,0) + coalesce(mc.base2_me,0) + coalesce(mc.base3_me,0) + coalesce(mc.cng_me,0) + coalesce(mc.isc_me,0) + 
			coalesce(mc.otros_me,0) + coalesce(mc.igv1_me,0) + coalesce(mc.igv2_me,0) + coalesce(mc.igv3_me,0) + coalesce(mc.icbper_me,0) END AS total,
			rc.name,
			coalesce(mc.base1_me,0) + coalesce(mc.base2_me,0) + coalesce(mc.base3_me,0) + coalesce(mc.cng_me,0) + coalesce(mc.isc_me,0) + 
			coalesce(mc.otros_me,0) + coalesce(mc.igv1_me,0) + coalesce(mc.igv2_me,0) + coalesce(mc.igv3_me,0) + coalesce(mc.icbper_me,0) AS monto_me,
			case when rc.name = 'PEN' then 1 else am.currency_rate end as currency_rate,
			am.date_detraccion AS fecha_det,
			am.voucher_number AS comp_det,
			dr.date AS f_doc_m,
			eic1.code AS td_doc_m,
			CASE
				WHEN split_part(dr.nro_comprobante, '-', 2) <> '' THEN split_part(dr.nro_comprobante, '-', 1)::character varying
				ELSE NULL
			END
			AS serie_m,
			CASE
				WHEN split_part(dr.nro_comprobante, '-', 2) <> '' THEN split_part(dr.nro_comprobante, '-', 2)::character varying
				ELSE split_part(dr.nro_comprobante, '-', 1)::character varying
			END
			AS numero_m,
			am.glosa,
			am.id AS am_id,
			rp.id AS partner_id
		   FROM account_move am
			 LEFT JOIN account_journal aj ON aj.id = am.journal_id
			 LEFT JOIN res_partner rp ON rp.id = am.partner_id
			 LEFT JOIN l10n_latam_identification_type lit ON lit.id = rp.l10n_latam_identification_type_id
			 LEFT JOIN l10n_latam_document_type ec1 ON ec1.id = am.l10n_latam_document_type_id
			 LEFT JOIN ( SELECT a2.type_document_id,
					a2.date,
					a2.nro_comprobante,
					a2.amount_currency,
					a2.amount,
					a2.bas_amount,
					a2.tax_amount,
					a2.id,
					a2.move_id
				   FROM doc_rela_pri a1
					 LEFT JOIN doc_invoice_relac a2 ON a1.min = a2.id) dr ON dr.move_id = am.id
			 LEFT JOIN l10n_latam_document_type eic1 ON eic1.id = dr.type_document_id
			 LEFT JOIN get_compras_1($1,$2,$3) mc ON mc.move_id = am.id
			 LEFT JOIN res_currency rc ON rc.id = am.currency_id
		  WHERE aj.register_sunat::text = '1'::text AND am.state::text = 'posted'::text
		  AND (am.date::date BETWEEN $1 and $2) AND am.company_id = $3
		  ORDER BY ("left"(to_char(am.date::timestamp with time zone, 'yyyymmdd'::text), 6)), aj.code, am.name;
END;
	$BODY$
	LANGUAGE plpgsql VOLATILE
	COST 100
	ROWS 1000;
--------------------------------------------------------------------------------------------------------------------------
DROP FUNCTION IF EXISTS public.get_compras_1_1_bm(date, date, integer) CASCADE;

CREATE OR REPLACE FUNCTION public.get_compras_1_1_bm(
	date_from date,
	date_to date,
	company_id integer)
	RETURNS TABLE(destino integer, moneda character varying, move_id integer, base1 numeric, base2 numeric, base3 numeric, cng numeric, igv1 numeric, igv2 numeric,
    igv3 numeric, icbper numeric, isc numeric, otros numeric, base1_me numeric, base2_me numeric, base3_me numeric, cng_me numeric, igv1_me numeric, igv2_me numeric,
    igv3_me numeric, icbper_me numeric, isc_me numeric, otros_me numeric) AS
	$BODY$
	BEGIN
	RETURN QUERY 
	SELECT
        CASE
            WHEN (((
            CASE
                WHEN a1.base1 <> 0::numeric THEN '1'::text
                ELSE '0'::text
            END ||
            CASE
                WHEN a1.base2 <> 0::numeric THEN '1'::text
                ELSE '0'::text
            END) ||
            CASE
                WHEN a1.base3 <> 0::numeric THEN '1'::text
                ELSE '0'::text
            END) ||
            CASE
                WHEN a1.cng <> 0::numeric THEN '1'::text
                ELSE '0'::text
            END) = '1000'::text THEN 1
            WHEN (((
            CASE
                WHEN a1.base1 <> 0::numeric THEN '1'::text
                ELSE '0'::text
            END ||
            CASE
                WHEN a1.base2 <> 0::numeric THEN '1'::text
                ELSE '0'::text
            END) ||
            CASE
                WHEN a1.base3 <> 0::numeric THEN '1'::text
                ELSE '0'::text
            END) ||
            CASE
                WHEN a1.cng <> 0::numeric THEN '1'::text
                ELSE '0'::text
            END) = '0100'::text THEN 2
            WHEN (((
            CASE
                WHEN a1.base1 <> 0::numeric THEN '1'::text
                ELSE '0'::text
            END ||
            CASE
                WHEN a1.base2 <> 0::numeric THEN '1'::text
                ELSE '0'::text
            END) ||
            CASE
                WHEN a1.base3 <> 0::numeric THEN '1'::text
                ELSE '0'::text
            END) ||
            CASE
                WHEN a1.cng <> 0::numeric THEN '1'::text
                ELSE '0'::text
            END) = '0010'::text THEN 3
            WHEN (((
            CASE
                WHEN a1.base1 <> 0::numeric THEN '1'::text
                ELSE '0'::text
            END ||
            CASE
                WHEN a1.base2 <> 0::numeric THEN '1'::text
                ELSE '0'::text
            END) ||
            CASE
                WHEN a1.base3 <> 0::numeric THEN '1'::text
                ELSE '0'::text
            END) ||
            CASE
                WHEN a1.cng <> 0::numeric THEN '1'::text
                ELSE '0'::text
            END) = '0001'::text THEN 4
            ELSE 5
        END AS destino,
    a3.name AS moneda,
    a1.move_id,
    a1.base1,
    a1.base2,
    a1.base3,
    a1.cng,
    a1.igv1,
    a1.igv2,
    a1.igv3,
    a1.icbper,
    a1.isc,
    a1.otros,
    a1.base1_me,
    a1.base2_me,
    a1.base3_me,
    a1.cng_me,
    a1.igv1_me,
    a1.igv2_me,
    a1.igv3_me,
    a1.icbper_me,
    a1.isc_me,
    a1.otros_me
   FROM get_compras_1($1,$2,$3) a1
     LEFT JOIN account_move a2 ON a2.id = a1.move_id
     LEFT JOIN res_currency a3 ON a3.id = a2.currency_id
  ORDER BY a1.move_id;
	END;
	$BODY$
	LANGUAGE plpgsql VOLATILE
	COST 100
	ROWS 1000;
--------------------------------------------------------------------------------------------------------------------------
DROP FUNCTION IF EXISTS public.get_compras_1_1_1_bm(date, date, integer) CASCADE;

CREATE OR REPLACE FUNCTION public.get_compras_1_1_1_bm(
	date_from date,
	date_to date,
	company_id integer)
	RETURNS TABLE(destino integer, moneda character varying, move_id integer, base1 numeric, base2 numeric, base3 numeric, cng numeric, igv1 numeric, igv2 numeric,
    igv3 numeric, icbper numeric, isc numeric, otros numeric) AS
	$BODY$
	BEGIN
	RETURN QUERY 
	SELECT bm11.destino,
    bm11.moneda,
    bm11.move_id,
        CASE
            WHEN bm11.moneda::text = 'PEN'::text THEN bm11.base1
            ELSE bm11.base1_me
        END AS base1,
        CASE
            WHEN bm11.moneda::text = 'PEN'::text THEN bm11.base2
            ELSE bm11.base2_me
        END AS base2,
        CASE
            WHEN bm11.moneda::text = 'PEN'::text THEN bm11.base3
            ELSE bm11.base3_me
        END AS base3,
        CASE
            WHEN bm11.moneda::text = 'PEN'::text THEN bm11.cng
            ELSE bm11.cng_me
        END AS cng,
        CASE
            WHEN bm11.moneda::text = 'PEN'::text THEN bm11.igv1
            ELSE bm11.igv1_me
        END AS igv1,
        CASE
            WHEN bm11.moneda::text = 'PEN'::text THEN bm11.igv2
            ELSE bm11.igv2_me
        END AS igv2,
        CASE
            WHEN bm11.moneda::text = 'PEN'::text THEN bm11.igv3
            ELSE bm11.igv3_me
        END AS igv3,
        CASE
            WHEN bm11.moneda::text = 'PEN'::text THEN bm11.icbper
            ELSE bm11.icbper_me
        END AS icbper,
        CASE
            WHEN bm11.moneda::text = 'PEN'::text THEN bm11.isc
            ELSE bm11.isc_me
        END AS isc,
        CASE
            WHEN bm11.moneda::text = 'PEN'::text THEN bm11.otros
            ELSE bm11.otros_me
        END AS otros
   FROM get_compras_1_1_bm($1,$2,$3) bm11;
	END;
	$BODY$
	LANGUAGE plpgsql VOLATILE
	COST 100
	ROWS 1000;
--------------------------------------------------------------------------------------------------------------------------
DROP FUNCTION IF EXISTS public.get_pdb_compras_1(date, date, integer) CASCADE;

CREATE OR REPLACE FUNCTION public.get_pdb_compras_1(
	date_from date,
	date_to date,
	company_id integer)
	RETURNS TABLE(move_id integer, destino integer, nro_destino integer, base numeric, igv numeric, isc numeric, otros numeric) AS
	$BODY$
	BEGIN
	RETURN QUERY 
	(SELECT bm111.move_id,
    bm111.destino,
    1 AS nro_destino,
    bm111.base1 AS base,
    bm111.igv1 AS igv,
    bm111.isc,
    bm111.otros
   FROM get_compras_1_1_1_bm($1,$2,$3) bm111
  WHERE bm111.base1 <> 0::numeric)
UNION ALL
 (SELECT bm111.move_id,
    bm111.destino,
    2 AS nro_destino,
    bm111.base2 AS base,
    bm111.igv2 AS igv,
    bm111.isc,
    bm111.otros
   FROM get_compras_1_1_1_bm($1,$2,$3) bm111
  WHERE bm111.base2 <> 0::numeric)
UNION ALL
 (SELECT bm111.move_id,
    bm111.destino,
    3 AS nro_destino,
    bm111.base3 AS base,
    bm111.igv3 AS igv,
    bm111.isc,
    bm111.otros
   FROM get_compras_1_1_1_bm($1,$2,$3) bm111
  WHERE bm111.base3 <> 0::numeric)
UNION ALL
 (SELECT bm111.move_id,
    bm111.destino,
    4 AS nro_destino,
    bm111.cng AS base,
    0 AS igv,
    bm111.isc,
    bm111.otros
   FROM get_compras_1_1_1_bm($1,$2,$3) bm111
  WHERE bm111.cng <> 0::numeric);
	END;
	$BODY$
	LANGUAGE plpgsql VOLATILE
	COST 100
	ROWS 1000;

--------------------------------------------------------------------------------------------------------------------------

DROP FUNCTION IF EXISTS public.get_pdb_compras_2(date, date, integer) CASCADE;

CREATE OR REPLACE FUNCTION public.get_pdb_compras_2(
	date_from date,
	date_to date,
	company_id integer)
	RETURNS TABLE(move_id integer, cod_destino integer, nro_destino integer, base numeric, igv numeric, isc numeric, otros numeric) AS
	$BODY$
	BEGIN
	RETURN QUERY 
	SELECT bm2.move_id,
    bm2.destino AS cod_destino,
        CASE
            WHEN bm2.destino <> 5 THEN 1
            ELSE bm2.nro_destino
        END AS nro_destino,
    bm2.base,
    bm2.igv,
        CASE
            WHEN min(bm2.nro_destino) OVER (PARTITION BY bm2.move_id) = bm2.nro_destino THEN bm2.isc
            ELSE 0::numeric
        END AS isc,
        CASE
            WHEN min(bm2.nro_destino) OVER (PARTITION BY bm2.move_id) = bm2.nro_destino THEN bm2.otros
            ELSE 0::numeric
        END AS otros
   FROM get_pdb_compras_1($1,$2,$3) bm2
  ORDER BY bm2.move_id, (
        CASE
            WHEN bm2.destino <> 5 THEN 1
            ELSE bm2.nro_destino
        END);
	END;
	$BODY$
	LANGUAGE plpgsql VOLATILE
	COST 100
	ROWS 1000;
	
--------------------------------------------------------------------------------------------------------------------------
DROP FUNCTION IF EXISTS public.get_recxhon_1(date, date, integer,character varying) CASCADE;

CREATE OR REPLACE FUNCTION public.get_recxhon_1(
	date_from date,
	date_to date,
	  company_id integer,
	by_date character varying)
	RETURNS TABLE(move_id integer, renta numeric, retencion numeric)  AS
	$BODY$
	BEGIN
	RETURN QUERY  
  	SELECT am.id as move_id,
	sum(
		CASE
			WHEN aat.record_fees::text = '1'::text THEN aml.tax_amount_it
			ELSE 0::numeric
		END) AS renta,
	sum(
		CASE
			WHEN aat.record_fees::text = '2'::text THEN aml.tax_amount_it
			ELSE 0::numeric
		END) AS retencion
   FROM account_move_line aml
	LEFT JOIN account_account_tag_account_move_line_rel rel ON rel.account_move_line_id = aml.id
	LEFT JOIN account_account_tag aat ON aat.id = rel.account_account_tag_id
	LEFT JOIN account_move am on am.id = aml.move_id
	WHERE aml.type_document_id = (SELECT account_main_parameter.td_recibos_hon
		   FROM account_main_parameter
		  WHERE account_main_parameter.company_id = $3) AND am.state::text = 'posted'::text AND aml.display_type IS NULL AND aml.account_id IS NOT NULL 
	AND ((CASE WHEN $4 = 'date' THEN am.date WHEN $4 = 'invoice_date_due' THEN am.invoice_date_due END) BETWEEN $1 and $2) AND am.company_id = $3
	AND rel.account_account_tag_id IS NOT NULL
  GROUP BY am.id;
 END;
	$BODY$
	LANGUAGE plpgsql VOLATILE
	COST 100
	ROWS 1000;
--------------------------------------------------------------------------------------------------------------------------
DROP FUNCTION IF EXISTS public.get_recxhon_1_1(date, date, integer,character varying) CASCADE;

CREATE OR REPLACE FUNCTION public.get_recxhon_1_1(
	  date_from date,
	date_to date,
	  company_id integer,
	by_date character varying)
	RETURNS TABLE(periodo integer, libro character varying,voucher character varying, fecha_doc date, fecha_e date, fecha_p date, td character varying,
	serie character varying,numero character varying,tdp character varying,docp character varying,apellido_p character varying,apellido_m character varying,namep character varying,
	divisa character varying, tipo_c numeric, renta numeric, retencion numeric, neto_p numeric,
	periodo_p character varying, is_not_home character varying, c_d_imp character varying, am_id integer) AS
	$BODY$
	BEGIN
	RETURN QUERY 
	SELECT CASE
	WHEN am.is_opening_close = true AND to_char(am.date::timestamp with time zone, 'mmdd'::text) = '0101'::text THEN (to_char(am.date::timestamp with time zone, 'yyyy'::text) || '00')::integer
	WHEN am.is_opening_close = true AND to_char(am.date::timestamp with time zone, 'mmdd'::text) = '1231'::text THEN (to_char(am.date::timestamp with time zone, 'yyyy'::text) || '13')::integer
	ELSE to_char(am.date::timestamp with time zone, 'yyyymm'::text)::integer
	END AS periodo,
	aj.code AS libro,
	am.name AS voucher,
	am.date AS fecha_doc,
	am.invoice_date AS fecha_e,
	am.invoice_date_due AS fecha_p,
	ec1.code AS td,
	CASE
		WHEN split_part(am.ref::text, '-'::text, 2) <> ''::text THEN split_part(am.ref::text, '-'::text, 1)::character varying
		ELSE ''::character varying
	END AS serie,
	CASE
		WHEN split_part(am.ref::text, '-'::text, 2) <> ''::text THEN split_part(am.ref::text, '-'::text, 2)::character varying
		ELSE split_part(am.ref::text, '-'::text, 1)::character varying
	END AS numero,
	lit.code_sunat AS tdp,
	rp.vat AS docp,
	rp.last_name AS apellido_p,
	rp.m_last_name AS apellido_m,
	rp.name_p AS namep,
	rc.name AS divisa,
	am.currency_rate AS tipo_c,
	rh.renta,
	rh.retencion,
	rh.renta + rh.retencion AS neto_p,
	to_char(am.invoice_date_due::timestamp with time zone, 'yyyymm'::text)::character varying AS periodo_p,
	CASE
		WHEN rp.is_not_home IS NULL OR rp.is_not_home = false THEN '1'::character varying
		ELSE '2'::character varying
	END AS is_not_home,
	rp.c_d_imp,
	am.id AS am_id
	FROM account_move am
	LEFT JOIN account_journal aj ON aj.id = am.journal_id
	LEFT JOIN res_partner rp ON rp.id = am.partner_id
	LEFT JOIN l10n_latam_identification_type lit ON lit.id = rp.l10n_latam_identification_type_id
	LEFT JOIN l10n_latam_document_type ec1 ON ec1.id = am.l10n_latam_document_type_id
	LEFT JOIN ( SELECT a2.type_document_id,
		  a2.date,
		  a2.nro_comprobante,
		  a2.amount_currency,
		  a2.amount,
		  a2.bas_amount,
		  a2.tax_amount,
		  a2.id,
		  a2.move_id
		  FROM doc_rela_pri a1
			LEFT JOIN doc_invoice_relac a2 ON a1.min = a2.id) dr ON dr.move_id = am.id
	LEFT JOIN l10n_latam_document_type eic1 ON eic1.id = dr.type_document_id
	LEFT JOIN get_recxhon_1($1,$2,$3,$4) rh ON rh.move_id = am.id
	LEFT JOIN res_currency rc ON rc.id = am.currency_id
	WHERE am.l10n_latam_document_type_id = ( SELECT account_main_parameter.td_recibos_hon
			FROM account_main_parameter
		  WHERE account_main_parameter.company_id = $3) AND am.state::text = 'posted'::text AND aj.type = 'purchase'
	AND ((CASE WHEN $4 = 'date' THEN am.date WHEN $4 = 'invoice_date_due' THEN am.invoice_date_due END) BETWEEN $1 and $2) AND am.company_id = $3
  ORDER BY to_char(am.date::timestamp with time zone, 'yyyymm'::text), aj.code, am.name;
 END;
	$BODY$
	LANGUAGE plpgsql VOLATILE
	COST 100
	ROWS 1000;

--------------------------------------------------------------------------------------------------------------------------
DROP FUNCTION IF EXISTS public.get_percepciones(date, date, integer) CASCADE;

CREATE OR REPLACE FUNCTION public.get_percepciones(
	  date_from date,
	date_to date,
	  company_id integer)
	RETURNS TABLE(periodo_con integer, periodo_percep integer, fecha_uso date, libro character varying, voucher character varying, tipo_per character varying, 
	ruc_agente character varying, partner character varying, tipo_comp character varying, serie_cp character varying, numero_cp character varying, 
	fecha_com_per date, percepcion numeric, t_comp character varying, serie_comp character varying, numero_comp character varying, 
	fecha_cp date, montof numeric) AS
	$BODY$
	BEGIN
	RETURN QUERY 
	SELECT CASE
		WHEN am.is_opening_close = true AND to_char(am.date::timestamp with time zone, 'mmdd'::text) = '0101'::text THEN (to_char(am.date::timestamp with time zone, 'yyyy'::text) || '00')::integer
		WHEN am.is_opening_close = true AND to_char(am.date::timestamp with time zone, 'mmdd'::text) = '1231'::text THEN (to_char(am.date::timestamp with time zone, 'yyyy'::text) || '13')::integer
		ELSE to_char(am.date::timestamp with time zone, 'yyyymm'::text)::integer
	END AS periodo_con,
	to_char(am.perception_date::timestamp with time zone, 'yyyymm'::text)::integer AS periodo_percep,
	am.perception_date AS fecha_uso,
	aj.code as libro,
	am.name as voucher,
	llit.code_sunat as tipo_per,
	rp.vat as ruc_agente,
	rp.name as partner,
	  lldt.code AS tipo_comp,
	CASE
		WHEN split_part(REPLACE(aml.nro_comp,'/','-')::text, '-'::text, 2) <> ''::text THEN split_part(REPLACE(aml.nro_comp,'/','-')::text, '-'::text, 1)::character varying
		ELSE ''::character varying
	END AS serie_cp,
	CASE
		WHEN split_part(REPLACE(aml.nro_comp,'/','-')::text, '-'::text, 2) <> ''::text THEN split_part(REPLACE(aml.nro_comp,'/','-')::text, '-'::text, 2)::character varying
		ELSE split_part(REPLACE(aml.nro_comp,'/','-')::text, '-'::text, 1)::character varying
	END AS numero_cp,
	am.invoice_date AS fecha_com_per,
	aml.tax_amount_it AS percepcion,
	dir.t_comp,
	CASE
		WHEN split_part(dir.nro_comprobante::text, '-'::text, 2) <> ''::text THEN split_part(dir.nro_comprobante::text, '-'::text, 1)::character varying
		ELSE ''::character varying
	END AS serie_comp,
	CASE
		WHEN split_part(dir.nro_comprobante::text, '-'::text, 2) <> ''::text THEN split_part(dir.nro_comprobante::text, '-'::text, 2)::character varying
		ELSE split_part(dir.nro_comprobante::text, '-'::text, 1)::character varying
	END AS numero_comp,
	dir.date AS fecha_cp,
	dir.amount AS montof
   FROM account_move_line aml
   LEFT JOIN account_move am on am.id = aml.move_id
   LEFT JOIN account_journal aj ON aj.id = am.journal_id
	LEFT JOIN res_partner rp ON rp.id = aml.partner_id
	LEFT JOIN l10n_latam_identification_type llit ON llit.id = rp.l10n_latam_identification_type_id
	LEFT JOIN l10n_latam_document_type lldt ON lldt.id = aml.type_document_id
	 LEFT JOIN ( SELECT b2.code,
			b1.date,
			b1.nro_comprobante,
			b1.amount,
			b1.amount_currency,
			b2.code as t_comp,
			b1.move_id
		   FROM doc_invoice_relac b1
			 LEFT JOIN l10n_latam_document_type b2 ON b2.id = b1.type_document_id) dir ON dir.move_id = aml.move_id
	LEFT JOIN account_account_tag_account_move_line_rel rel ON rel.account_move_line_id = aml.id
  	WHERE rel.account_account_tag_id = (select prm.tax_account
						from account_main_parameter prm where prm.company_id = $3)
		and am.company_id = $3 and (am.perception_date::date between $1 and $2);
END;
	$BODY$
	LANGUAGE plpgsql VOLATILE
	COST 100
	ROWS 1000;
--------------------------------------------------------------------------------------------------------------------------
DROP FUNCTION IF EXISTS public.get_percepciones_sp(date, date, integer) CASCADE;

CREATE OR REPLACE FUNCTION public.get_percepciones_sp(
	  date_from date,
	date_to date,
	  company_id integer)
	RETURNS TABLE(periodo_con integer, periodo_percep integer, fecha_uso date, libro character varying, voucher character varying, 
	tipo_per character varying, ruc_agente character varying, partner character varying, tipo_comp character varying, serie_cp character varying, 
	numero_cp character varying, fecha_com_per date, percepcion numeric) AS
	$BODY$
	BEGIN
	RETURN QUERY 
	 SELECT
	CASE
		WHEN am.is_opening_close = true AND to_char(am.date::timestamp with time zone, 'mmdd'::text) = '0101'::text THEN (to_char(am.date::timestamp with time zone, 'yyyy'::text) || '00')::integer
		WHEN am.is_opening_close = true AND to_char(am.date::timestamp with time zone, 'mmdd'::text) = '1231'::text THEN (to_char(am.date::timestamp with time zone, 'yyyy'::text) || '13')::integer
		ELSE to_char(am.date::timestamp with time zone, 'yyyymm'::text)::integer
	END AS periodo_con,
	to_char(am.perception_date::timestamp with time zone, 'yyyymm'::text)::integer AS periodo_percep,
	am.perception_date AS fecha_uso,
	aj.code as libro,
	am.name as voucher,
	llit.code_sunat as tipo_per,
	rp.vat as ruc_agente,
	rp.name as partner,
	  lldt.code AS tipo_comp,
	CASE
		WHEN split_part(REPLACE(aml.nro_comp,'/','-')::text, '-'::text, 2) <> ''::text THEN split_part(REPLACE(aml.nro_comp,'/','-')::text, '-'::text, 1)::character varying
		ELSE ''::character varying
	END AS serie_cp,
	CASE
		WHEN split_part(REPLACE(aml.nro_comp,'/','-')::text, '-'::text, 2) <> ''::text THEN split_part(REPLACE(aml.nro_comp,'/','-')::text, '-'::text, 2)::character varying
		ELSE split_part(REPLACE(aml.nro_comp,'/','-')::text, '-'::text, 1)::character varying
	END AS numero_cp,
	am.invoice_date AS fecha_com_per,
	aml.tax_amount_it AS percepcion
	FROM account_move_line aml
	LEFT JOIN account_move am on am.id = aml.move_id
	LEFT JOIN account_journal aj ON aj.id = am.journal_id
	LEFT JOIN res_partner rp ON rp.id = aml.partner_id
	LEFT JOIN l10n_latam_identification_type llit ON llit.id = rp.l10n_latam_identification_type_id
	LEFT JOIN l10n_latam_document_type lldt ON lldt.id = aml.type_document_id
  	LEFT JOIN account_account_tag_account_move_line_rel rel ON rel.account_move_line_id = aml.id
  	WHERE rel.account_account_tag_id = (select prm.tax_account
						from account_main_parameter prm where prm.company_id = $3)
		and am.company_id = $3 and (am.perception_date::date between $1 and $2);
END;
	$BODY$
	LANGUAGE plpgsql VOLATILE
	COST 100
	ROWS 1000;
--------------------------------------------------------------------------------------------------------------------------

DROP FUNCTION IF EXISTS public.get_destinos(integer,integer,integer) CASCADE;

  CREATE OR REPLACE FUNCTION public.get_destinos(
	IN var_periodo_from integer,
	IN var_periodo_to integer,
	IN var_company_id integer)
  RETURNS TABLE(periodo character varying, fecha date, libro character varying, voucher character varying, cuenta character varying, debe numeric, haber numeric, balance numeric, cta_analitica character varying, des_debe character varying, des_haber character varying, am_id integer, aml_id integer, company_id integer) AS
$BODY$
BEGIN
RETURN QUERY 

SELECT T.* FROM(SELECT a1.periodo::character varying,
	a1.fecha,
	a1.libro,
	a1.voucher,
	a1.cuenta,
	a1.debe,
	a1.haber,
	a1.balance,
	a5.code AS cta_analitica,
	a3.code AS des_debe,
	a4.code AS des_haber,
	a1.move_id AS am_id,
	a1.move_line_id AS aml_id,
	$2 as company_id
   FROM get_diariog((select date_start from account_period where code = $1::character varying limit 1),(select date_end from account_period where code = $2::character varying  limit 1),$3) a1
	 LEFT JOIN account_account a2 ON a2.id = a1.account_id
	 LEFT JOIN account_account a3 ON a3.id = a2.a_debit
	 LEFT JOIN account_account a4 ON a4.id = a2.a_credit
	 LEFT JOIN account_analytic_account a5 ON a5.id = a1.analytic_account_id
  WHERE a2.check_moorage = true AND (a3.code::text || a4.code::text) IS NOT NULL AND (a1.periodo between $1 and $2)
UNION ALL
 SELECT b7.periodo::character varying,
	b7.fecha,
	b7.libro,
	b7.voucher,
	b7.cuenta,
		CASE
			WHEN b1.amount < 0::numeric THEN abs(b1.amount)
			ELSE 0::numeric
		END AS debe,
		CASE
			WHEN b1.amount > 0::numeric THEN b1.amount
			ELSE 0::numeric
		END AS haber,
	b7.balance,
	b4.code AS cta_analitica,
	b5.code AS des_debe,
	b6.code AS des_haber,
	b7.move_id AS am_id,
	b7.move_line_id AS aml_id,
	$2 as company_id
   FROM account_analytic_line b1
	 LEFT JOIN account_move_line b2 ON b2.id = b1.move_id
	 LEFT JOIN account_account b3 ON b3.id = b1.general_account_id
	 LEFT JOIN account_analytic_account b4 ON b4.id = b1.account_id
	 LEFT JOIN account_account b5 ON b5.id = b4.a_debit
	 LEFT JOIN account_account b6 ON b6.id = b4.a_credit
	 LEFT JOIN get_diariog((select date_start from account_period where code = $1::character varying  limit 1),(select date_end from account_period where code = $2::character varying  limit 1),$3) b7 ON b7.move_line_id = b1.move_id
  WHERE b3.check_moorage = true AND (b7.periodo between $1 and $2) AND b2.company_id = $3) T
  WHERE T.des_debe IS NOT NULL AND T.des_haber IS NOT NULL;
END;
$BODY$
LANGUAGE plpgsql VOLATILE
COST 100
ROWS 1000;
----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

DROP FUNCTION IF EXISTS public.get_summary_destinos(integer,integer) CASCADE;

  CREATE OR REPLACE FUNCTION public.get_summary_destinos(
	IN var_periodo integer,
	IN var_company_id integer)
  RETURNS TABLE(cuenta character varying, balance numeric, cta20 numeric, cta24 numeric, cta25 numeric, cta26 numeric, cta90 numeric, cta91 numeric, cta92 numeric, cta93 numeric, cta94 numeric, cta95 numeric, cta96 numeric, cta97 numeric, cta98 numeric, cta99 numeric) AS
$BODY$
BEGIN
RETURN QUERY 
SELECT
vst_d.cuenta,
sum(vst_d.debe-vst_d.haber) as balance,
sum(CASE WHEN left(vst_d.des_debe,2)='20'  THEN (vst_d.debe-vst_d.haber) ELSE 0 END)AS cta20,
sum(CASE WHEN left(vst_d.des_debe,2)='24'  THEN (vst_d.debe-vst_d.haber) ELSE 0 END) AS cta24,
sum(CASE WHEN left(vst_d.des_debe,2)='25'  THEN (vst_d.debe-vst_d.haber) ELSE 0 END) AS cta25,
sum(CASE WHEN left(vst_d.des_debe,2)='26'  THEN (vst_d.debe-vst_d.haber) ELSE 0 END) AS cta26,
sum(CASE WHEN left(vst_d.des_debe,2)='90'  THEN (vst_d.debe-vst_d.haber) ELSE 0 END) AS cta90,
sum(CASE WHEN left(vst_d.des_debe,2)='91'  THEN (vst_d.debe-vst_d.haber) ELSE 0 END) AS cta91,
sum(CASE WHEN left(vst_d.des_debe,2)='92'  THEN (vst_d.debe-vst_d.haber) ELSE 0 END) AS cta92,
sum(CASE WHEN left(vst_d.des_debe,2)='93'  THEN (vst_d.debe-vst_d.haber) ELSE 0 END) AS cta93,
sum(CASE WHEN left(vst_d.des_debe,2)='94'  THEN (vst_d.debe-vst_d.haber) ELSE 0 END) AS cta94,
sum(CASE WHEN left(vst_d.des_debe,2)='95'  THEN (vst_d.debe-vst_d.haber) ELSE 0 END) AS cta95,
sum(CASE WHEN left(vst_d.des_debe,2)='96'  THEN (vst_d.debe-vst_d.haber) ELSE 0 END) AS cta96,
sum(CASE WHEN left(vst_d.des_debe,2)='97'  THEN (vst_d.debe-vst_d.haber) ELSE 0 END) AS cta97,
sum(CASE WHEN left(vst_d.des_debe,2)='98'  THEN (vst_d.debe-vst_d.haber) ELSE 0 END) AS cta98,
sum(CASE WHEN left(vst_d.des_debe,2)='99'  THEN (vst_d.debe-vst_d.haber) ELSE 0 END) AS cta99
FROM get_destinos($1,$1,$2) vst_d
group by vst_d.cuenta;
END;
$BODY$
LANGUAGE plpgsql VOLATILE
COST 100
ROWS 1000;

-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

DROP FUNCTION IF EXISTS public.get_asiento_destino(integer, integer) CASCADE;

CREATE OR REPLACE FUNCTION public.get_asiento_destino(
	IN var_periodo integer,
	IN var_company_id integer)
  RETURNS TABLE(periodo integer, glosa text,cuenta character varying, name character varying, debe numeric, haber numeric, account_id integer) AS
$BODY$
BEGIN
RETURN QUERY 
select $1::integer as periodo, 'Por el destino del Periodo ' || $1 as glosa, T.cuenta, aa.name, T.debe, T.haber, aa.id as account_id from (
select 
vst_d.des_debe as cuenta,
sum(vst_d.debe) as debe,
0:: numeric as haber
from get_destinos($1,$1,$2) vst_d
group by vst_d.des_debe

union all

select vst_d.des_haber as cuenta,
0::numeric as debe,
sum(vst_d.debe) as haber
from get_destinos($1,$1,$2) vst_d
group by vst_d.des_haber

union all

select vst_d.des_debe as cuenta,
0::numeric as debe,
sum(vst_d.haber) as haber
from get_destinos($1,$1,$2) vst_d
group by vst_d.des_debe

union all

select vst_d.des_haber as cuenta,
sum(vst_d.haber) as debe,
0::numeric as haber
from get_destinos($1,$1,$2) vst_d
group by vst_d.des_haber)T
left join (select * from account_account where company_id=$2) aa on aa.code = T.cuenta 
where (T.debe+T.haber) <> 0;
END;
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100
  ROWS 1000;