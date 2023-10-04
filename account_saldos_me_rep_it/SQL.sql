CREATE OR REPLACE FUNCTION public.get_saldos_me_rep(
	period_from character varying,
	period_to character varying,
	company_id integer)
    RETURNS TABLE(cuenta character varying, denominacion character varying, moneda character varying, debe numeric, haber numeric, saldo numeric,
    debe_me numeric, haber_me numeric, saldo_me numeric, account_id integer) 
    LANGUAGE 'plpgsql'
    COST 100
    VOLATILE PARALLEL UNSAFE
    ROWS 1000

AS $BODY$
BEGIN
	RETURN QUERY 
select a2.code as cuenta, a2.name as denominacion, coalesce(rc.name,'PEN') as moneda,sum(a1.debit) as debe,sum(a1.credit) as haber, sum(a1.debit-a1.credit) as saldo,
sum(case when a1.amount_currency>0 then a1.amount_currency else 0 end) as debe_me,
sum(case when a1.amount_currency<0 then abs(a1.amount_currency) else 0 end) as haber_me, 
sum(a1.amount_currency) as saldo_me, a1.account_id
from account_move_line a1
left join account_account a2 on a2.id=a1.account_id
left join account_move a3 on a3.id=a1.move_id 
left join res_currency rc on rc.id = a2.currency_id
where a2.currency_id is not null and a1.company_id=$3 and ( periodo_de_fecha(a3.date,a3.is_opening_close) between $1::integer and $2::integer) and a3.state='posted' and a1.display_type is null
group by a1.account_id, a2.code, a2.name, coalesce(rc.name,'PEN');
  END;
$BODY$;