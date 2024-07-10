
DROP FUNCTION IF EXISTS public.get_f2_register_balance_inventory(character varying,integer) CASCADE;

CREATE OR REPLACE FUNCTION public.get_f2_register_balance_inventory(
	IN period character varying,
	IN date_to date,
	IN company integer)
    RETURNS TABLE(mayor text, cuenta character varying, nomenclatura character varying, debe_inicial numeric, haber_inicial numeric, debe numeric, haber numeric, saldo_deudor numeric, saldo_acreedor numeric, activo numeric, pasivo numeric, perdinat numeric, ganannat numeric, perdifun numeric, gananfun numeric, rubro character varying) 
    LANGUAGE 'plpgsql'

    COST 100
    VOLATILE 
    ROWS 1000
    
AS $BODY$
BEGIN
RETURN QUERY 
	select 
		left(cta.code,2) as mayor,
		cta.code as cuenta,
		cta.name as nomenclatura,
		t.debeini as debe_inicial,
		t.haberini as haber_inicial,
		t.debep as debe,
		t.haberp as haber,
		t.saldo_deudor,
		t.saldo_acreedor,
		case 
			when t.saldo_deudor > 0 and cta.clasification_sheet = '0'
			then t.saldo_deudor
			else 0.00
		end as activo,
		case 
			when t.saldo_acreedor > 0 and cta.clasification_sheet = '0'
			then t.saldo_acreedor
			else 0.00
		end as pasivo,
		case 
			when (t.saldo_deudor > 0 and cta.clasification_sheet = '1') or 
					(t.saldo_deudor > 0 and cta.clasification_sheet = '3')
			then t.saldo_deudor
			else 0.00
		end as perdinat,
		case 
			when (t.saldo_acreedor > 0 and cta.clasification_sheet = '1') or
					(t.saldo_acreedor > 0 and cta.clasification_sheet = '3')
			then t.saldo_acreedor
			else 0.00
		end as ganannat,
		case 
			when (t.saldo_deudor > 0 and cta.clasification_sheet = '2') or
					(t.saldo_deudor > 0 and cta.clasification_sheet = '3')
			then T.saldo_deudor
			else 0.00
		end as perdifun,
		case 
			when (t.saldo_acreedor > 0 and cta.clasification_sheet = '2') or
					(t.saldo_acreedor > 0 and cta.clasification_sheet = '3')
			then t.saldo_acreedor
			else 0.00
		end as gananfun,
		tipo.name as rubro
		from (select 
		distinct aml.account_id,
		coalesce(saldoini.debeini,0.00) as debeini,
		coalesce(saldoini.haberini,0.00) as haberini,
		coalesce(saldoac.debeac,0.00) as debep,
		coalesce(saldoac.haberac,0.00) as haberp,
		case when 
			coalesce(saldoini.debeini,0.00)+ coalesce(saldoac.debeac,0.00) > coalesce(saldoini.haberini,0.00)+ coalesce(saldoac.haberac,0.00)
		then
			(coalesce(saldoini.debeini,0.00)+ coalesce(saldoac.debeac,0.00)) - (coalesce(saldoini.haberini,0.00)+ coalesce(saldoac.haberac,0.00))
		else 0.00
		end as saldo_deudor,
		case when 
			  coalesce(saldoini.haberini,0.00)+ coalesce(saldoac.haberac,0.00) > coalesce(saldoini.debeini,0.00)+ coalesce(saldoac.debeac,0.00)
		then 
			 ( coalesce(saldoini.haberini,0.00)+ coalesce(saldoac.haberac,0.00)) - (coalesce(saldoini.debeini,0.00)+ coalesce(saldoac.debeac,0.00))
		else 0.00
		end as saldo_acreedor
		from account_move_line aml 
		LEFT JOIN account_move am ON am.id = aml.move_id
		left join 
		(SELECT aml.account_id,
		(case when sum(aml.debit) - sum(aml.credit) > 0 then sum(aml.debit) - sum(aml.credit) else 0 end) AS debeini,
		(case when sum(aml.debit) - sum(aml.credit) < 0 then abs(sum(aml.debit) - sum(aml.credit)) else 0 end) AS haberini
		FROM account_move_line aml
		LEFT JOIN account_move am ON am.id = aml.move_id
		WHERE aml.company_id = $3
		AND (CASE
			WHEN am.is_opening_close = true AND to_char(am.date::timestamp with time zone, 'mmdd'::text) = '0101'::text THEN to_char(am.date::timestamp with time zone, 'yyyy'::text) || '00'::text
			WHEN am.is_opening_close = true AND to_char(am.date::timestamp with time zone, 'mmdd'::text) = '1231'::text THEN to_char(am.date::timestamp with time zone, 'yyyy'::text) || '13'::text
			ELSE to_char(am.date::timestamp with time zone, 'yyyymm'::text)
			END::integer = (left($1,4) || '00')::integer) 
			AND am.state = 'posted'
			AND aml.display_type IS NULL
		group by aml.account_id) saldoini on saldoini.account_id=aml.account_id
		left join 
		(SELECT aml.account_id,
		sum(aml.debit) AS debeac,
		sum(aml.credit) AS haberac
		FROM account_move_line aml 
		LEFT JOIN account_move am ON am.id = aml.move_id
		where aml.company_id = $3 AND (CASE
			WHEN am.is_opening_close = true AND to_char(am.date::timestamp with time zone, 'mmdd'::text) = '0101'::text THEN to_char(am.date::timestamp with time zone, 'yyyy'::text) || '00'::text
			WHEN am.is_opening_close = true AND to_char(am.date::timestamp with time zone, 'mmdd'::text) = '1231'::text THEN to_char(am.date::timestamp with time zone, 'yyyy'::text) || '13'::text
			ELSE to_char(am.date::timestamp with time zone, 'yyyymm'::text)
			END::integer BETWEEN (left($1,4) || '01')::integer AND $1::integer)
		AND (am.date <= $2::date)
		AND (CASE
			WHEN am.is_opening_close = true AND to_char(am.date::timestamp with time zone, 'mmdd'::text) = '0101'::text THEN to_char(am.date::timestamp with time zone, 'yyyy'::text) || '00'::text
			WHEN am.is_opening_close = true AND to_char(am.date::timestamp with time zone, 'mmdd'::text) = '1231'::text THEN to_char(am.date::timestamp with time zone, 'yyyy'::text) || '13'::text
			ELSE to_char(am.date::timestamp with time zone, 'yyyymm'::text)
			END::integer <> (left($1,4) || '00')::integer)
		AND am.state = 'posted'
		AND aml.display_type IS NULL
		group by aml.account_id) saldoac on saldoac.account_id=aml.account_id
		where aml.company_id=$3 and (CASE
			WHEN am.is_opening_close = true AND to_char(am.date::timestamp with time zone, 'mmdd'::text) = '0101'::text THEN to_char(am.date::timestamp with time zone, 'yyyy'::text) || '00'::text
			WHEN am.is_opening_close = true AND to_char(am.date::timestamp with time zone, 'mmdd'::text) = '1231'::text THEN to_char(am.date::timestamp with time zone, 'yyyy'::text) || '13'::text
			ELSE to_char(am.date::timestamp with time zone, 'yyyymm'::text)
			END::integer BETWEEN (left($1,4) || '00')::integer AND $1::integer)
			AND (am.date <= $2::date)
			AND am.state = 'posted'
			AND aml.display_type IS NULL) t
		left join account_account cta on cta.id=t.account_id                 
		left join account_type_it tipo on tipo.id=cta.account_type_it_id
		order by left(cta.code,2),cta.code;              
END; 
$BODY$;