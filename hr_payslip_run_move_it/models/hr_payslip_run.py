# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError
from datetime import *

class HrResumenPlanilla(models.Model):
	_inherit = 'hr.payslip.run'

	account_move_id = fields.Many2one('account.move', string='Asiento Contable', readonly=True)

	def action_open_asiento(self):
		self.ensure_one()
		return {
			"type": "ir.actions.act_window",
			"res_model": "account.move",
			"views": [[False, "tree"], [False, "form"]],
			"domain": [['id', '=', self.account_move_id.id]],
			"name": "Asiento de Planillas",
		}

	def get_sql(self):
		struct_id=self.env['hr.payroll.structure'].search([('schedule_pay', '=', 'monthly'),('active', '=',True),('company_id', '=', self.env.company.id)],limit=1).id
		SalaryRules = self.env['hr.salary.rule'].search([('is_detail_cta', '=', True), ('struct_id', '=', struct_id)], order='sequence')
		if SalaryRules:
			# print("SalaryRules.mapped('code')",len(SalaryRules.mapped('code')))
			if len(SalaryRules.mapped('code')) == 1:
				codes = str(tuple(SalaryRules.mapped('code')))
				codes = "%s" %(codes.replace(',)',')'))
				codes_afp = "('COMFI','COMMIX','SEGI','A_JUB' %s" %(codes.replace('(',','))
				codes_afp = "%s" %(codes_afp.replace(',)',')'))
			else:
				codes = str(tuple(SalaryRules.mapped('code')))
				codes_afp = "('COMFI','COMMIX','SEGI','A_JUB' %s" %(codes.replace('(',','))
		else:
			codes = "('')"
			codes_afp = "('COMFI','COMMIX','SEGI','A_JUB')"
		# print("codes",codes)
		# print("codes_afp",codes_afp)
		sql = """
				DROP VIEW IF EXISTS hr_payslip_run_move;
				CREATE OR REPLACE VIEW hr_payslip_run_move AS
				(
					SELECT row_number() OVER () AS id, T.* FROM (
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
    where prm.payslip_run_id = {payslip_run_id} and
    prm.company_id = {company} and
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
        where hsr.code not in {codes_afp} and
        prm.payslip_run_id = {payslip_run_id} and
        prm.company_id = {company} and
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
        case when hsr.code in {codes} then prm.total else 0 end credit,
        hr_employee.address_home_id as partner_id
        from payslip_run_move prm
        inner join hr_salary_rule hsr on hsr.id = prm.salary_rule_id
        left join hr_contract on prm.contract_id = hr_contract.id
        left join hr_employee on hr_contract.employee_id =  hr_employee.id
        where hsr.code in {codes} and
        prm.payslip_run_id = {payslip_run_id} and
        prm.company_id = {company} and
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
    prm.payslip_run_id = {payslip_run_id} and
    prm.company_id = {company} and
    hm.account_id is not null
    group by hc.membership_id,hm.name, hm.account_id
					)T
					where T.debit!=0 or T.credit!=0
				)
			""".format(
				payslip_run_id = self.id,
				company = self.env.company.id,
				codes_afp = codes_afp,
				codes = codes
		)
		# print("sql",sql)
		return sql

	def get_move_wizard(self):
		if len(self.ids) > 1:
			raise UserError('No se puede seleccionar mas de un registro para este proceso')
		if self.account_move_id:
			raise UserError('Elimine el Asiento Actual para generar uno nuevo')
		self._cr.execute(self.get_sql())
		lines = self.env['hr.payslip.run.move'].search([])
		# print("lines",lines)
		total_credit = total_debit = 0
		for line in lines:
			total_credit += line.credit
			total_debit += line.debit
		return {
			'name': 'Generar Asiento Contable',
			'type': 'ir.actions.act_window',
			'res_model': 'hr.payslip.run.move.wizard',
			'views': [(self.env.ref('hr_payslip_run_move_it.payslip_run_generation_move_wizard_form').id, 'form')],
			'context': {'default_credit': total_credit,
						'default_debit': total_debit,
						'payslip_run_id': self.id},
			'target': 'new'
		}