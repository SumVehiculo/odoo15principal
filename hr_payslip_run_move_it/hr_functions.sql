---------------------------- Asiento Contable de Nomina -------------------------------------
DROP VIEW IF EXISTS payslip_run_move cascade;
CREATE OR REPLACE VIEW public.payslip_run_move
    AS
	select distinct
	hsr.sequence,
	hsr.id as salary_rule_id,
	hsr.name AS description,
	hp.id as slip_id,
	hp.payslip_run_id,
	hsr.company_id,
	CASE
        WHEN ipd.value_reference IS NOT NULL THEN split_part(ipd.value_reference::text, ','::text, 2)::integer
        ELSE NULL::integer
    END AS account_debit,
    CASE
        WHEN ipc.value_reference IS NOT NULL THEN split_part(ipc.value_reference::text, ','::text, 2)::integer
        ELSE NULL::integer
    END AS account_credit,
	hpl.total,
    hp.contract_id
	from hr_payslip_line hpl
	inner join hr_payslip hp on hp.id = hpl.slip_id
	inner join hr_salary_rule hsr on hsr.id = hpl.salary_rule_id
	inner join ir_model_fields imfd ON imfd.model::text = 'hr.salary.rule'::text AND imfd.name::text = 'account_debit'::text
	inner join ir_model_fields imfc ON imfc.model::text = 'hr.salary.rule'::text AND imfc.name::text = 'account_credit'::text
	left join ir_property ipd ON ipd.res_id::text = ('hr.salary.rule,'::text || hsr.id) AND imfd.id = ipd.fields_id
	left join ir_property ipc ON ipc.res_id::text = ('hr.salary.rule,'::text || hsr.id) AND imfc.id = ipc.fields_id;

---------------------------- Asiento Contable sin Distribucion -------------------------------------
DROP FUNCTION IF EXISTS public.payslip_run_move(integer,integer) cascade;
CREATE OR REPLACE FUNCTION payslip_run_move(
	payslip_run integer,
	company integer)
	RETURNS TABLE(sequence integer, salary_rule_id integer, description character varying, analytic_account_id integer,
	        account_id integer, debit numeric, credit numeric, partner_id integer)
	LANGUAGE 'plpgsql'

	COST 100
	VOLATILE 
	ROWS 1000
AS $BODY$
BEGIN

RETURN QUERY

	select distinct
	prm.sequence,
	prm.salary_rule_id,
	prm.description,
	0 as analytic_account_id,
	prm.account_debit as account_id,
	round(sum(prm.total)::numeric, 2) as debit,
	0::numeric as credit,
	null::integer as partner_id
	from payslip_run_move prm
	where prm.payslip_run_id = $1 and
	prm.company_id = $2 and
	prm.account_debit is not null
	group by prm.sequence, prm.salary_rule_id, prm.description, prm.account_debit

	union all

	select distinct
	prm.sequence,
	prm.salary_rule_id,
	prm.description,
	0 as analytic_account_id,
	prm.account_credit as account_id,
	0::numeric as debit,
	round(sum(prm.total)::numeric, 2) as credit,
	null::integer as partner_id
	from payslip_run_move prm
	inner join hr_salary_rule hsr on hsr.id = prm.salary_rule_id
	where hsr.code not in ('COMFI','COMMIX','SEGI','A_JUB') and
	prm.payslip_run_id = $1 and
	prm.company_id = $2 and
	prm.account_credit is not null
	group by prm.sequence, prm.salary_rule_id, prm.description, prm.account_credit

	union all

	select distinct
	58 as sequence,
	hc.membership_id as salary_rule_id,
	hm.name as description,
	0 as analytic_account_id,
	hm.account_id as account_id,
	0::numeric as debit,
	round(sum(prm.total)::numeric, 2) as credit,
	null::integer as partner_id
	from payslip_run_move prm
	inner join hr_payslip hp on hp.id = prm.slip_id
	inner join hr_contract hc on hc.id = hp.contract_id
	inner join hr_membership hm on hm.id = hc.membership_id
	inner join hr_salary_rule hsr on hsr.id = prm.salary_rule_id
	where hsr.code in ('COMFI','COMMIX','SEGI','A_JUB') and
	prm.payslip_run_id = $1 and
	prm.company_id = $2 and
	hm.account_id is not null
	group by hc.membership_id,hm.name, hm.account_id;

END;
$BODY$;

---------------------------- Asiento Contable Detallado de Nomina -------------------------------------

DROP FUNCTION IF EXISTS public.payslip_run_analytic_move(integer,integer) cascade;
CREATE OR REPLACE FUNCTION payslip_run_analytic_move(
	payslip_run integer,
    company integer)
    RETURNS TABLE(sequence integer, salary_rule_id integer, description character varying,analytic_account_id integer,
                    account_id integer, debit numeric, credit numeric, partner_id integer)
    LANGUAGE 'plpgsql'

    COST 100
    VOLATILE
    ROWS 1000
AS $BODY$
BEGIN

RETURN QUERY

    select
    lo.sequence,
    lo.salary_rule_id,
    lo.description,
    lo.analytic_account_id,
    lo.account_id as account_id,
    sum(lo.debit) as debit,
    sum(lo.credit) as credit,
    lo.partner_id
    from (
    select distinct
    prm.sequence,
    prm.salary_rule_id,
    prm.description,
    CASE WHEN aa.check_moorage THEN aaa.id ELSE 0 END AS analytic_account_id,
--    aaa.id as analytic_account_id,
    prm.account_debit as account_id,
    CASE WHEN aa.check_moorage THEN round(sum(prm.total * hadl.percent * 0.01)::numeric, 2) ELSE round(sum(prm.total)::numeric, 2) END AS debit,
--    round(sum(prm.total * hadl.percent * 0.01)::numeric, 2) as debit,
    0::numeric as credit,
    null::integer as partner_id
    from payslip_run_move prm
    inner join hr_payslip hp on hp.id = prm.slip_id
    inner join hr_contract hc on hc.id = hp.contract_id
    inner join hr_analytic_distribution had on had.id = hc.distribution_id
    inner join hr_analytic_distribution_line hadl on hadl.distribution_id = had.id
    inner join account_analytic_account aaa on aaa.id = hadl.analytic_id
    left join account_account aa on prm.account_debit =aa.id
    where prm.payslip_run_id = $1 and
    prm.company_id = $2 and
    prm.account_debit is not null
    group by prm.sequence, prm.salary_rule_id,prm.description,aa.check_moorage, aaa.id, prm.account_debit
    ) lo
    group by
    lo.sequence,
    lo.salary_rule_id,
    lo.description,
    lo.analytic_account_id,
    lo.account_id,
    lo.partner_id

    union all

    select
    lo.sequence,
    lo.salary_rule_id,
    lo.description,
    lo.analytic_account_id,
    lo.account_id as account_id,
    sum(lo.debit) as debit,
    sum(lo.credit) as credit,
    lo.partner_id
    from (
        select distinct
        hp.id,
        prm.sequence,
        prm.salary_rule_id,
        hsr.name as description,
        CASE WHEN aa.check_moorage THEN aaa.id ELSE 0 END AS analytic_account_id,
--        0 as analytic_account_id,
        prm.account_credit as account_id,
        0::numeric as debit,
        CASE WHEN aa.check_moorage THEN round((prm.total * hadl.percent * 0.01)::numeric, 2) ELSE round(prm.total::numeric, 2) END AS credit,
--        round(total::numeric, 2) as credit,
        null::integer as partner_id
        from payslip_run_move prm
        inner join hr_salary_rule hsr on hsr.id = prm.salary_rule_id
        inner join hr_payslip hp on hp.id = prm.slip_id
        inner join hr_contract hc on hc.id = hp.contract_id
        inner join hr_analytic_distribution had on had.id = hc.distribution_id
        inner join hr_analytic_distribution_line hadl on hadl.distribution_id = had.id
        inner join account_analytic_account aaa on aaa.id = hadl.analytic_id
        left join account_account aa on prm.account_credit = aa.id
        where hsr.code not in ('COMFI','COMMIX','SEGI','A_JUB') and
        prm.payslip_run_id = $1 and
        prm.company_id = $2 and
        prm.account_credit is not null

        union all

        select
        0 as id,
        prm.sequence,
        prm.salary_rule_id,
        hsr.name as description,
        0 as analytic_account_id,
        prm.account_credit as account_id,
        0::numeric as debit,
        case when hsr.code in ('') then prm.total else 0 end credit,
        hr_employee.address_home_id as partner_id
        from payslip_run_move prm
        inner join hr_salary_rule hsr on hsr.id = prm.salary_rule_id
        left join hr_contract on prm.contract_id = hr_contract.id
        left join hr_employee on hr_contract.employee_id =  hr_employee.id
        where hsr.code in ('') and
        prm.payslip_run_id = $1 and
        prm.company_id = $2 and
        prm.account_credit is not null

    ) lo
    group by
    lo.sequence,
    lo.salary_rule_id,
    lo.description,
    lo.analytic_account_id,
    lo.account_id,
    lo.partner_id

    union all
    select distinct
    58 as sequence,
    hc.membership_id as salary_rule_id,
    hm.name as description,
    0 as analytic_account_id,
    hm.account_id as account_id,
    0::numeric as debit,
    round(sum(prm.total)::numeric, 2) as credit,
    null::integer as partner_id
    from payslip_run_move prm
    inner join hr_payslip hp on hp.id = prm.slip_id
    inner join hr_contract hc on hc.id = hp.contract_id
    inner join hr_membership hm on hm.id = hc.membership_id
    inner join hr_salary_rule hsr on hsr.id = prm.salary_rule_id
    where hsr.code in ('COMFI','COMMIX','SEGI','A_JUB') and
    prm.payslip_run_id = $1 and
    prm.company_id = $2 and
    hm.account_id is not null
    group by hc.membership_id,hm.name, hm.account_id;

END;
$BODY$;

