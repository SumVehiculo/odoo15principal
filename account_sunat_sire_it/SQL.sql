DROP FUNCTION IF EXISTS public.get_compras_1_sunat(date, date, integer, character varying) CASCADE;

CREATE OR REPLACE FUNCTION public.get_compras_1_sunat(
	date_from date,
	date_to date,
	company_id integer,
    date_type character varying)
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
	WHERE am.state::text = 'posted'::text AND aml.display_type IS NULL AND aml.account_id IS NOT NULL AND 
    ((case when $4 = 'date' then am.date::date else am.date_modify_purchase::date end) BETWEEN $1 and $2) AND am.company_id = $3
	AND aj.register_sunat = '1' AND rel.account_account_tag_id IS NOT NULL
	GROUP BY am.id;
END;
	$BODY$
	LANGUAGE plpgsql VOLATILE
	COST 100
	ROWS 1000;
--------------------------------------------------------------------------------------------------------------------------
DROP FUNCTION IF EXISTS public.get_compras_1_1_sunat(date, date, integer,character varying) CASCADE;

CREATE OR REPLACE FUNCTION public.get_compras_1_1_sunat(
	date_from date,
	date_to date,
	company_id integer,
    date_type character varying)
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
			coalesce(mc.base1,0),
			coalesce(mc.base2,0),
			coalesce(mc.base3,0),
			coalesce(mc.cng,0),
			coalesce(mc.isc,0),
			coalesce(mc.otros,0),
			coalesce(mc.igv1,0),
			coalesce(mc.igv2,0),
			coalesce(mc.igv3,0),
			coalesce(mc.icbper,0),
			coalesce(mc.base1,0) + coalesce(mc.base2,0) + coalesce(mc.base3,0) + coalesce(mc.cng,0) + coalesce(mc.isc,0) + coalesce(mc.otros,0) + 
			coalesce(mc.igv1,0) + coalesce(mc.igv2,0) + coalesce(mc.igv3,0) + coalesce(mc.icbper,0) AS total,
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
			 LEFT JOIN get_compras_1_sunat($1,$2,$3,$4) mc ON mc.move_id = am.id
			 LEFT JOIN res_currency rc ON rc.id = am.currency_id
		  WHERE aj.register_sunat::text = '1'::text AND am.state::text = 'posted'::text
		  AND ((case when $4 = 'date' then am.date::date else am.date_modify_purchase::date end) BETWEEN $1 and $2) AND am.company_id = $3
		  ORDER BY ("left"(to_char(am.date::timestamp with time zone, 'yyyymmdd'::text), 6)), aj.code, am.name;
END;
	$BODY$
	LANGUAGE plpgsql VOLATILE
	COST 100
	ROWS 1000;

-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------
------------------------------------------------------------------------------------VENTAS-----------------------------------------------------------------------------------
--------------------------------------------------------------------------------------------------------------------------
DROP FUNCTION IF EXISTS public.get_ventas_1_sunat(date, date, integer, character varying) CASCADE;

CREATE OR REPLACE FUNCTION public.get_ventas_1_sunat(
	date_from date,
	date_to date,
	company_id integer,
    date_type character varying)
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
	WHERE am.state::text = 'posted'::text AND aml.display_type IS NULL AND aml.account_id IS NOT NULL 
	AND ((case when $4 = 'date' then am.date::date else am.date_modify_sale::date end) BETWEEN $1 and $2) AND am.company_id = $3
	AND aj.register_sunat = '2' AND rel.account_account_tag_id IS NOT NULL
	GROUP BY am.id;
END;
	$BODY$
	LANGUAGE plpgsql VOLATILE
	COST 100
	ROWS 1000;
--------------------------------------------------------------------------------------------------------------------------
DROP FUNCTION IF EXISTS public.get_ventas_1_1_sunat(date, date, integer, character varying) CASCADE;

CREATE OR REPLACE FUNCTION public.get_ventas_1_1_sunat(
	date_from date,
	date_to date,
	company_id integer,
    date_type character varying)
RETURNS TABLE(periodo integer, fecha_cont date,libro character varying, voucher character varying, fecha_e date, fecha_v date,
	td character varying, serie character varying, anio character varying, numero character varying, tdp character varying, docp character varying,
	namep character varying, exp numeric, venta_g numeric, inaf numeric, exo numeric, isc_v numeric, otros_v numeric, igv_v numeric, icbper numeric,
	total numeric, name character varying, monto_me numeric, currency_rate numeric, fecha_det date, comp_det character varying, f_doc_m date,
	td_doc_m character varying, serie_m character varying, numero_m character varying, glosa character varying, estado_ple character varying, am_id integer) AS
	$BODY$
	BEGIN
	RETURN QUERY 
	SELECT CASE
		WHEN am.is_opening_close = true AND to_char((case when $4 = 'date' then am.date::date else am.date_modify_sale::date end)::timestamp with time zone, 'mmdd'::text) = '0101'::text THEN (to_char((case when $4 = 'date' then am.date::date else am.date_modify_sale::date end)::timestamp with time zone, 'yyyy'::text) || '00')::integer
		WHEN am.is_opening_close = true AND to_char((case when $4 = 'date' then am.date::date else am.date_modify_sale::date end)::timestamp with time zone, 'mmdd'::text) = '1231'::text THEN (to_char((case when $4 = 'date' then am.date::date else am.date_modify_sale::date end)::timestamp with time zone, 'yyyy'::text) || '13')::integer
		ELSE to_char((case when $4 = 'date' then am.date::date else am.date_modify_sale::date end)::timestamp with time zone, 'yyyymm'::text)::integer
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
			coalesce(mv.exp,0) as exp,
			coalesce(mv.venta_g,0) as venta_g,
			coalesce(mv.inaf,0) as inaf,
			coalesce(mv.exo,0) as exo,
			coalesce(mv.isc_v,0) as isc_v,
			coalesce(mv.otros_v,0) as otros_v,
			coalesce(mv.igv_v,0) as igv_v,
			coalesce(mv.icbper,0) as icbper,
			
			(coalesce(mv.exp,0) + coalesce(mv.venta_g,0) + coalesce(mv.inaf,0) + coalesce(mv.exo,0) + coalesce(mv.isc_v,0) + 
			coalesce(mv.otros_v,0) + coalesce(mv.igv_v,0) + coalesce(mv.icbper,0)) AS total,
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
			 LEFT JOIN get_ventas_1_sunat($1,$2,$3,$4) mv ON mv.move_id = am.id
			 LEFT JOIN res_currency rc ON rc.id = am.currency_id
		  WHERE aj.register_sunat::text = '2'::text AND am.state::text = 'posted'::text
		  AND ( (case when $4 = 'date' then am.date::date else am.date_modify_sale::date end) BETWEEN $1 and $2) AND am.company_id = $3
		  ORDER BY ("left"(to_char(am.date::timestamp with time zone, 'yyyymmdd'::text), 6)), aj.code, am.name;
END;
	$BODY$
	LANGUAGE plpgsql VOLATILE
	COST 100
	ROWS 1000;
--------------------------------------------------------------------------------------------------------------------------