DROP FUNCTION IF EXISTS public.get_diariog_usd(character varying, character varying, integer,integer[]) CASCADE;

CREATE OR REPLACE FUNCTION public.get_diariog_usd(
    period_to character varying,
	period_from character varying,
	company_id integer,
  	not_journal_ids integer[])
    RETURNS TABLE(periodo character varying, fecha date, libro character varying, voucher character varying, cuenta character varying, debe numeric, haber numeric, debe_me numeric, haber_me numeric, balance numeric, 
    moneda character varying, tc numeric, importe_me numeric, cta_analitica character varying, glosa character varying, td_partner character varying, doc_partner character varying, partner character varying, 
    td_sunat character varying, nro_comprobante character varying, fecha_doc date, fecha_ven date, col_reg character varying, monto_reg numeric, medio_pago character varying, ple_diario character varying, ple_compras character varying,
    ple_ventas character varying, move_id integer, move_line_id integer, account_id integer, analytic_account_id integer, partner_id integer) AS
    $BODY$
    BEGIN
    RETURN QUERY 
    SELECT
    CASE
        WHEN am.is_opening_close = true AND to_char(am.date::timestamp with time zone, 'mmdd'::text) = '0101'::text THEN (to_char(am.date::timestamp with time zone, 'yyyy'::text) || '00')::character varying
        WHEN am.is_opening_close = true AND to_char(am.date::timestamp with time zone, 'mmdd'::text) = '1231'::text THEN (to_char(am.date::timestamp with time zone, 'yyyy'::text) || '13')::character varying
        ELSE to_char(am.date::timestamp with time zone, 'yyyymm'::text)::character varying
    END AS periodo,
    am.date AS fecha,
    aj.code AS libro,
    am.name AS voucher,
    aa.code AS cuenta,
    aml.debit AS debe,
    aml.credit AS haber,
    case when aml.amount_c > 0 then aml.amount_c else 0 end as debe_me,
    case when aml.amount_c < 0 then abs(aml.amount_c) else 0 end as haber_me,
    aml.balance,
    CASE
        WHEN aml.currency_id IS NULL THEN 'PEN'::character varying
        ELSE rc.name
    END AS moneda,
    coalesce(case when aml.tc = 0 then 1 else aml.tc end,1) as tc,
    aml.amount_c AS importe_me,
    ana.code AS cta_analitica,
    am.glosa,
    llit.code_sunat AS td_partner,
    rp.vat AS doc_partner,
    rp.name AS partner,
    ec1.code AS td_sunat,
    REPLACE(aml.nro_comp,'/','-')::character varying AS nro_comprobante,
    am.invoice_date AS fecha_doc,
    aml.date_maturity AS fecha_ven,
    aat.name AS col_reg,
    aml.tax_amount_it AS monto_reg,
    ecp.code AS medio_pago,
    am.ple_state AS ple_diario,
    am.campo_41_purchase AS ple_compras,
    am.campo_34_sale AS ple_ventas,
    am.id AS move_id,
    aml.id AS move_line_id,
    aml.account_id,
    aml.analytic_account_id,
    aml.partner_id
    FROM account_move am
        LEFT JOIN account_move_line aml ON aml.move_id = am.id
        LEFT JOIN account_journal aj ON aj.id = am.journal_id
        LEFT JOIN account_account aa ON aa.id = aml.account_id
        LEFT JOIN res_currency rc ON rc.id = aml.currency_id
        LEFT JOIN res_partner rp ON rp.id = aml.partner_id
        LEFT JOIN l10n_latam_identification_type llit ON llit.id = rp.l10n_latam_identification_type_id
        LEFT JOIN l10n_latam_document_type ec1 ON ec1.id = aml.type_document_id
        LEFT JOIN account_account_tag_account_move_line_rel rel ON rel.account_move_line_id = aml.id
        LEFT JOIN account_account_tag aat ON aat.id = rel.account_account_tag_id
        LEFT JOIN account_analytic_account ana ON ana.id = aml.analytic_account_id
        LEFT JOIN einvoice_catalog_payment ecp ON ecp.id = am.td_payment_id
    WHERE am.state::text = 'posted'::text AND aml.display_type IS NULL AND aml.account_id IS NOT NULL AND am.journal_id <> ANY($4)
    AND (CASE
        WHEN am.is_opening_close = true AND to_char(am.date::timestamp with time zone, 'mmdd'::text) = '0101'::text THEN (to_char(am.date::timestamp with time zone, 'yyyy'::text) || '00')::integer
        WHEN am.is_opening_close = true AND to_char(am.date::timestamp with time zone, 'mmdd'::text) = '1231'::text THEN (to_char(am.date::timestamp with time zone, 'yyyy'::text) || '13')::integer
        ELSE to_char(am.date::timestamp with time zone, 'yyyymm'::text)::integer
    END BETWEEN $1::integer and $2::integer) AND am.company_id = $3
    ORDER BY (date_part('month'::text, am.date)), aj.code, am.name, aml.debit DESC, aa.code;
    END;
    $BODY$
    LANGUAGE plpgsql VOLATILE
    COST 100
    ROWS 1000;
--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

DROP FUNCTION IF EXISTS public.get_f1_register_usd(character varying,character varying,integer,integer[]) CASCADE;

CREATE OR REPLACE FUNCTION public.get_f1_register_usd(
    IN period_from character varying,
    IN period_to character varying,
    IN company integer,
  	not_journal_ids integer[])
  RETURNS TABLE(account_id integer, mayor text, cuenta character varying, nomenclatura character varying, debe numeric, haber numeric, saldo_deudor numeric, saldo_acreedor numeric, activo numeric, pasivo numeric, perdinat numeric, ganannat numeric, perdifun numeric, gananfun numeric, rubro character varying) AS
$BODY$
BEGIN

RETURN QUERY 
    
	select T.account_id, left(aa.code,2) as mayor,aa.code as cuenta,aa.name as nomenclatura,T.debe,T.haber,
		   T.saldo_deudor,T.saldo_acreedor,
	case 
		when T.saldo_deudor > 0 and aa.clasification_sheet = '0'
		then T.saldo_deudor
		else 0
	end as activo,
	case 
		when T.saldo_acreedor > 0 and aa.clasification_sheet = '0'
		then T.saldo_acreedor
		else 0
	end as pasivo,
	case 
		when (T.saldo_deudor > 0 and aa.clasification_sheet = '1') or 
			 (T.saldo_deudor > 0 and aa.clasification_sheet = '3')
		then T.saldo_deudor
		else 0
	end as perdinat,
	case 
		when (T.saldo_acreedor > 0 and aa.clasification_sheet = '1') or
			 (T.saldo_acreedor > 0 and aa.clasification_sheet = '3')
		then T.saldo_acreedor
		else 0
	end as ganannat,
	case 
		when (T.saldo_deudor > 0 and aa.clasification_sheet = '2') or
			 (T.saldo_deudor > 0 and aa.clasification_sheet = '3')
		then T.saldo_deudor
		else 0
	end as perdifun,
	case 
		when (T.saldo_acreedor > 0 and aa.clasification_sheet = '2') or
			 (T.saldo_acreedor > 0 and aa.clasification_sheet = '3')
		then T.saldo_acreedor
		else 0
	end as gananfun,
	ati.name as rubro
	from(select
		aml.account_id,
		sum(coalesce((case when aml.amount_c > 0 then aml.amount_c else 0 end),0)) as debe,
		sum(coalesce((case when aml.amount_c < 0 then abs(aml.amount_c) else 0 end),0)) as haber,
		case 
			when sum(coalesce((case when aml.amount_c > 0 then aml.amount_c else 0 end),0)) > sum(coalesce((case when aml.amount_c < 0 then abs(aml.amount_c) else 0 end),0))
			then sum(coalesce((case when aml.amount_c > 0 then aml.amount_c else 0 end),0)) - sum(coalesce((case when aml.amount_c < 0 then abs(aml.amount_c) else 0 end),0))
			else 0
		end as saldo_deudor,
		case
			when sum(coalesce((case when aml.amount_c < 0 then abs(aml.amount_c) else 0 end),0)) > sum(coalesce((case when aml.amount_c > 0 then aml.amount_c else 0 end),0))
			then sum(coalesce((case when aml.amount_c < 0 then abs(aml.amount_c) else 0 end),0)) - sum(coalesce((case when aml.amount_c > 0 then aml.amount_c else 0 end),0))
			else 0
		end as saldo_acreedor
		from account_move_line aml
		LEFT JOIN account_move am ON am.id = aml.move_id
        WHERE am.state::text = 'posted'::text AND aml.display_type IS NULL AND aml.account_id IS NOT NULL AND am.journal_id <> ANY($4)
        AND (CASE
            WHEN am.is_opening_close = true AND to_char(am.date::timestamp with time zone, 'mmdd'::text) = '0101'::text THEN (to_char(am.date::timestamp with time zone, 'yyyy'::text) || '00')::integer
            WHEN am.is_opening_close = true AND to_char(am.date::timestamp with time zone, 'mmdd'::text) = '1231'::text THEN (to_char(am.date::timestamp with time zone, 'yyyy'::text) || '13')::integer
            ELSE to_char(am.date::timestamp with time zone, 'yyyymm'::text)::integer
        END BETWEEN $1::integer and $2::integer) AND am.company_id = $3
		group by aml.account_id)T
	left join account_account aa on aa.id = T.account_id
	left join account_type_it ati on ati.id = aa.account_type_it_id
	order by left(aa.code,2),aa.code;
                  
END; $BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100
  ROWS 1000;

---------------------------------------------------------------------------------------------------------------------------------------------------------------------------

DROP FUNCTION IF EXISTS public.get_f1_balance_usd(character varying,character varying,integer,integer[]) CASCADE;

CREATE OR REPLACE FUNCTION public.get_f1_balance_usd(
    IN period_from character varying,
    IN period_to character varying,
    IN company integer,
  	not_journal_ids integer[])
  RETURNS TABLE(mayor text, nomenclatura character varying, debe numeric, haber numeric, saldo_deudor numeric, saldo_acreedor numeric, activo numeric, pasivo numeric, perdinat numeric, ganannat numeric, perdifun numeric, gananfun numeric) AS
$BODY$
BEGIN

RETURN QUERY 
    
	select T.mayor,T.name,T.debe,T.haber,
		   T.saldo_deudor,T.saldo_acreedor,
	case 
		when T.saldo_deudor > 0 and ag.clasification_sheet = '0'
		then T.saldo_deudor
		else 0
	end as activo,
	case 
		when T.saldo_acreedor > 0 and ag.clasification_sheet = '0'
		then T.saldo_acreedor
		else 0
	end as pasivo,
	case 
		when (T.saldo_deudor > 0 and ag.clasification_sheet = '1') or 
			 (T.saldo_deudor > 0 and ag.clasification_sheet = '3')
		then T.saldo_deudor
		else 0
	end as perdinat,
	case 
		when (T.saldo_acreedor > 0 and ag.clasification_sheet = '1') or
			 (T.saldo_acreedor > 0 and ag.clasification_sheet = '3')
		then T.saldo_acreedor
		else 0
	end as ganannat,
	case 
		when (T.saldo_deudor > 0 and ag.clasification_sheet = '2') or
			 (T.saldo_deudor > 0 and ag.clasification_sheet = '3')
		then T.saldo_deudor
		else 0
	end as perdifun,
	case 
		when (T.saldo_acreedor > 0 and ag.clasification_sheet = '2') or
			 (T.saldo_acreedor > 0 and ag.clasification_sheet = '3')
		then T.saldo_acreedor
		else 0
	end as gananfun
	from(select
        left(aa.code,2) as mayor,
		ag.name,
		ag.id,
		sum(coalesce((case when aml.amount_c > 0 then aml.amount_c else 0 end),0)) as debe,
		sum(coalesce((case when aml.amount_c < 0 then abs(aml.amount_c) else 0 end),0)) as haber,
		case 
			when sum(coalesce((case when aml.amount_c > 0 then aml.amount_c else 0 end),0)) > sum(coalesce((case when aml.amount_c < 0 then abs(aml.amount_c) else 0 end),0))
			then sum(coalesce((case when aml.amount_c > 0 then aml.amount_c else 0 end),0)) - sum(coalesce((case when aml.amount_c < 0 then abs(aml.amount_c) else 0 end),0))
			else 0
		end as saldo_deudor,
		case
			when sum(coalesce((case when aml.amount_c < 0 then abs(aml.amount_c) else 0 end),0)) > sum(coalesce((case when aml.amount_c > 0 then aml.amount_c else 0 end),0))
			then sum(coalesce((case when aml.amount_c < 0 then abs(aml.amount_c) else 0 end),0)) - sum(coalesce((case when aml.amount_c > 0 then aml.amount_c else 0 end),0))
			else 0
		end as saldo_acreedor
		from account_move_line aml
		LEFT JOIN account_move am ON am.id = aml.move_id
        LEFT JOIN account_account aa ON aa.id = aml.account_id
        LEFT JOIN account_group ag ON ag.code_prefix = left(aa.code,2)
        WHERE am.state::text = 'posted'::text AND aml.display_type IS NULL AND aml.account_id IS NOT NULL AND am.journal_id <> ANY($4)
        AND (CASE
            WHEN am.is_opening_close = true AND to_char(am.date::timestamp with time zone, 'mmdd'::text) = '0101'::text THEN (to_char(am.date::timestamp with time zone, 'yyyy'::text) || '00')::integer
            WHEN am.is_opening_close = true AND to_char(am.date::timestamp with time zone, 'mmdd'::text) = '1231'::text THEN (to_char(am.date::timestamp with time zone, 'yyyy'::text) || '13')::integer
            ELSE to_char(am.date::timestamp with time zone, 'yyyymm'::text)::integer
        END BETWEEN $1::integer and $2::integer) AND am.company_id = $3
		group by left(aa.code,2),ag.name,ag.id)T
	inner join account_group ag on ag.id = T.id
	order by T.mayor;
                  
END; $BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100
  ROWS 1000;

------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
DROP FUNCTION IF EXISTS public.get_saldos_me_global_usd(character varying,character varying,integer,integer[]) CASCADE;

CREATE OR REPLACE FUNCTION public.get_saldos_me_global_usd(
	periodo_apertura character varying,
	periodo character varying,
	company_id integer,
  	not_journal_ids integer[])
    RETURNS TABLE(account_id integer, saldomn numeric, saldome numeric, tc numeric) 
    LANGUAGE 'plpgsql'

    COST 100
    VOLATILE 
    ROWS 1000
AS $BODY$
BEGIN
	RETURN QUERY   
	SELECT a1.account_id,
		sum(coalesce(a1.balance,0)) AS saldomn,
		round(sum(coalesce(a1.importe_me,0)),2) AS saldome,
		CASE
            WHEN ad.rate_type = 'purchase' THEN ( SELECT edcl.compra
               FROM exchange_diff_config_line edcl
                 LEFT JOIN exchange_diff_config edc ON edc.id = edcl.line_id
                 LEFT JOIN account_period ap ON ap.id = edcl.period_id
              WHERE edc.company_id = $3 AND ap.code = $2)
            ELSE ( SELECT edcl.venta
               FROM exchange_diff_config_line edcl
                 LEFT JOIN exchange_diff_config edc ON edc.id = edcl.line_id
                 LEFT JOIN account_period ap ON ap.id = edcl.period_id
              WHERE edc.company_id = $3 AND ap.code = $2)
        END AS tc
	   	FROM get_diariog_usd($1,$2,$3,$4) a1
		LEFT JOIN account_account a2 ON a2.id = a1.account_id
		LEFT JOIN adjustment_account_account ad ON ad.account_id = a1.account_id
	  	WHERE ad.adjustment_type = 'global'
	  	GROUP BY a1.account_id,ad.rate_type;
END;
$BODY$;
--------------------------------------------------------------------------------------------------------------------------------------
DROP FUNCTION IF EXISTS public.get_saldos_me_global_final_usd(character varying,character varying,integer,integer[]) CASCADE;

CREATE OR REPLACE FUNCTION public.get_saldos_me_global_final_usd(
	fiscal_year character varying,
	periodo character varying,
	company_id integer,
  	not_journal_ids integer[])
    RETURNS TABLE(account_id integer, saldomn numeric, saldome numeric, tc numeric, saldo_act numeric, diferencia numeric, difference_account_id integer) 
    LANGUAGE 'plpgsql'

    COST 100
    VOLATILE 
    ROWS 1000
AS $BODY$
BEGIN
	RETURN QUERY  
	SELECT vst.account_id, vst.saldomn, vst.saldome, vst.tc,
	round(vst.saldomn/coalesce(vst.tc,1),2)::numeric  AS saldo_act,
	(round(vst.saldomn/coalesce(vst.tc,1),2) - vst.saldome)::numeric AS diferencia,
	CASE 
	WHEN (round(vst.saldomn/coalesce(vst.tc,1),2) - vst.saldome) > 0 AND ad.rate_type = 'purchase' THEN (SELECT edc.profit_account_id FROM exchange_diff_config edc WHERE edc.company_id = $3)
	WHEN (round(vst.saldomn/coalesce(vst.tc,1),2) - vst.saldome) < 0 AND ad.rate_type = 'purchase' THEN (SELECT edc.loss_account_id FROM exchange_diff_config edc WHERE edc.company_id = $3)
	WHEN (round(vst.saldomn/coalesce(vst.tc,1),2) - vst.saldome) > 0 AND ad.rate_type = 'sale' THEN (SELECT edc.profit_account_id FROM exchange_diff_config edc WHERE edc.company_id = $3)
	WHEN (round(vst.saldomn/coalesce(vst.tc,1),2) - vst.saldome) < 0 AND ad.rate_type = 'sale' THEN (SELECT edc.loss_account_id FROM exchange_diff_config edc WHERE edc.company_id = $3) 
	END AS difference_account_id
	FROM get_saldos_me_global_usd($1||'00',$2,$3,$4) vst
	LEFT JOIN adjustment_account_account ad ON ad.account_id = vst.account_id
	WHERE (round(vst.saldomn/coalesce(vst.tc,1),2) - vst.saldome) <> 0;
END;
$BODY$;

----------------------------------------------------------------------------------------------------------------------------------------------------------
DROP FUNCTION IF EXISTS public.get_saldos_me_documento_usd(character varying,character varying,integer,integer[]) CASCADE;

CREATE OR REPLACE FUNCTION public.get_saldos_me_documento_usd(
	periodo_apertura character,
	periodo character,
	company_id integer,
  	not_journal_ids integer[])
    RETURNS TABLE(partner_id integer, account_id integer, td_sunat character varying, nro_comprobante character varying, saldomn numeric, saldome numeric, tc numeric) 
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
	sum(coalesce(a1.balance,0))as saldomn,
	round(sum(coalesce(a1.importe_me,0)),2) as saldome,
	CASE
		WHEN ad.rate_type = 'purchase' THEN ( SELECT edcl.compra
			FROM exchange_diff_config_line edcl
				LEFT JOIN exchange_diff_config edc ON edc.id = edcl.line_id
				LEFT JOIN account_period ap ON ap.id = edcl.period_id
			WHERE edc.company_id = $3 AND ap.code = $2)
		ELSE ( SELECT edcl.venta
			FROM exchange_diff_config_line edcl
				LEFT JOIN exchange_diff_config edc ON edc.id = edcl.line_id
				LEFT JOIN account_period ap ON ap.id = edcl.period_id
			WHERE edc.company_id = $3 AND ap.code = $2)
	END AS tc
	from get_diariog_usd($1,$2,$3,$4) a1
	left join account_account a2 on a2.id=a1.account_id
	LEFT JOIN adjustment_account_account ad ON ad.account_id = a1.account_id
	left join res_currency a4 on a4.id = a2.currency_id
	WHERE ad.adjustment_type = 'documento' and
	a1.td_sunat is not null and
	a1.nro_comprobante is not null
	group by a1.partner_id,a1.account_id,ad.rate_type,a1.td_sunat,a1.nro_comprobante
	having (sum(a1.balance)+sum(a1.importe_me)) <> 0;
END;
$BODY$;

--------------------------------------------------------------------------------------------------------------------------------------

DROP FUNCTION IF EXISTS public.get_saldos_me_documento_final_usd(character varying,character varying,integer,integer[]) CASCADE;

CREATE OR REPLACE FUNCTION public.get_saldos_me_documento_final_usd(
	fiscal_year character varying,
	periodo character varying,
	company_id integer,
  	not_journal_ids integer[])
    RETURNS TABLE(partner_id integer, account_id integer, td_sunat character varying, nro_comprobante character varying, saldomn numeric, saldome numeric, tc numeric, saldo_act numeric, diferencia numeric, difference_account_id integer) 
    LANGUAGE 'plpgsql'

    COST 100
    VOLATILE 
    ROWS 1000
AS $BODY$
BEGIN
	RETURN QUERY  
	SELECT vst.partner_id, vst.account_id, vst.td_sunat, vst.nro_comprobante, vst.saldomn, vst.saldome, vst.tc,
	round(vst.saldomn/coalesce(vst.tc,1),2)::numeric AS saldo_act,
	(round(vst.saldomn/coalesce(vst.tc,1),2) - vst.saldome)::numeric  AS diferencia,
	CASE 
	WHEN (round(vst.saldomn/coalesce(vst.tc,1),2) - vst.saldome) > 0 AND ad.rate_type = 'purchase' THEN (SELECT edc.profit_account_id FROM exchange_diff_config edc WHERE edc.company_id = $3)::integer
	WHEN (round(vst.saldomn/coalesce(vst.tc,1),2) - vst.saldome) < 0 AND ad.rate_type = 'purchase' THEN (SELECT edc.loss_account_id FROM exchange_diff_config edc WHERE edc.company_id = $3)::integer
	WHEN (round(vst.saldomn/coalesce(vst.tc,1),2) - vst.saldome) > 0 AND ad.rate_type = 'sale' THEN (SELECT edc.profit_account_id FROM exchange_diff_config edc WHERE edc.company_id = $3)::integer
	WHEN (round(vst.saldomn/coalesce(vst.tc,1),2) - vst.saldome) < 0 AND ad.rate_type = 'sale' THEN (SELECT edc.loss_account_id FROM exchange_diff_config edc WHERE edc.company_id = $3)::integer
	END AS difference_account_id
	FROM get_saldos_me_documento_usd($1||'00',$2,$3,$4) vst
	LEFT JOIN adjustment_account_account ad ON ad.account_id = vst.account_id
	WHERE (round(vst.saldomn/coalesce(vst.tc,1),2) - vst.saldome) <> 0;
END;
$BODY$;
--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
DROP FUNCTION IF EXISTS public.get_saldos_usd(date, date, integer) CASCADE;

CREATE OR REPLACE FUNCTION public.get_saldos_usd(
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
to_char((case when b2.fecha_contable is null then am.date else b2.fecha_contable end)::timestamp with time zone, 'yyyy/mm/dd'::text) AS fecha_con,
aj.code as libro,
am.name as voucher,
lit.code_sunat as td_partner,
rp.vat as doc_partner,
rp.name as partner,
ec1.code as td_sunat,
b1.nro_comp as nro_comprobante,
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
sum(a1.amount_c) as saldo_me,
array_agg(a1.id) as aml_ids
from account_move_line a1
left join account_move a2 on a2.id=a1.move_id
left join account_account a3 on a3.id=a1.account_id
where a3.is_document_an=TRUE and a2.state='posted' and (a2.date between $1 and $2) and a1.company_id=$3
group by a1.partner_id,a1.account_id,a1.type_document_id,a1.nro_comp)b1

left join
(
select a2.id as move_id,a1.id as move_line_id,a1.account_id,a1.partner_id,a1.type_document_id,a1.nro_comp,
a2.date as fecha_contable,
a2.invoice_date as fecha_emision,
a1.date_maturity as fecha_vencimiento,
a2.glosa as glosa,
a1.debit-a1.credit as monto_ini_mn,a1.amount_c as monto_ini_me,
a2.currency_id
from account_move_line a1
left join account_move a2 on a2.id=a1.move_id
left join account_account a3 on a3.id=a1.account_id
where a2.move_type in ('out_receipt','in_receipt','out_invoice','in_invoice','out_refund','in_refund') and
a3.internal_type in ('payable','receivable') and a2.state='posted' and a1.company_id=$3
)b2 on (b2.account_id=b1.account_id and b2.partner_id=b1.partner_id and b2.type_document_id=b1.type_document_id and b2.nro_comp=b1.nro_comp)
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