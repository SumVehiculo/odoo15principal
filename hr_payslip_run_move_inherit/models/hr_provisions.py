# -*- coding:utf-8 -*-
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
import base64
from odoo.tools import date_utils

class HrProvisiones(models.Model):
	_inherit = 'hr.provisiones'

	def get_move_lines(self):
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		if MainParameter.detallar_provision:
			sql_provision = """
							union all
							select 
							lo.account_id,
							lo.description,
							null::integer as analytic_account_id,
        					null::integer as analytic_tag_id,
							sum(lo.debit) as debit,
							sum(lo.credit) as credit,
							lo.partner_id
							from (
								select 
									hpro.cts_haber as account_id,
									'Provision de CTS a Pagar'::text as description,
									0::numeric as debit,
									round(hpcl.provisiones_cts::numeric, 2) as credit,
									he.address_home_id as partner_id
									from hr_provisiones_cts_line hpcl
									inner join hr_provisiones hpro ON hpro.id = hpcl.provision_id
									inner join hr_payslip_run hpr on hpr.id = hpro.payslip_run_id
									left join hr_contract hc on hc.id = hpcl.contract_id
									left join hr_employee he on he.id = hc.employee_id
									where hpro.company_id = {company}
									and hpr.id = {payslip_run_id}
									and hpro.id = {provision_id}
								union all
								select 
									hpro.grati_haber as account_id,
									'Provision de Gratificacion a Pagar'::text as description,
									0::numeric as debit,
									round(hpgl.provisiones_grati::numeric, 2) as credit,
									he.address_home_id as partner_id
									from hr_provisiones_grati_line hpgl
									inner join hr_provisiones hpro ON hpro.id = hpgl.provision_id
									inner join hr_payslip_run hpr on hpr.id = hpro.payslip_run_id
									left join hr_contract hc on hc.id = hpgl.contract_id
									left join hr_employee he on he.id = hc.employee_id
									where hpro.company_id = {company}
									and hpr.id = {payslip_run_id}
									and hpro.id = {provision_id}
								union all
								select 
									hpro.boni_haber as account_id,
									'Provision de Gratificacion a Pagar'::text as description,
									0::numeric as debit,
									round(hpgl.boni_grati::numeric, 2) as credit,
									he.address_home_id as partner_id
									from hr_provisiones_grati_line hpgl
									inner join hr_provisiones hpro ON hpro.id = hpgl.provision_id
									inner join hr_payslip_run hpr on hpr.id = hpro.payslip_run_id
									left join hr_contract hc on hc.id = hpgl.contract_id
									left join hr_employee he on he.id = hc.employee_id
									where hpro.company_id = {company}
									and hpr.id = {payslip_run_id}
									and hpro.id = {provision_id}
								union all
								select 
									hpro.vaca_haber as account_id,
									'Provision de Vacaciones a Pagar'::text as description,
									0::numeric as debit,
									round(hpvl.provisiones_vaca::numeric, 2) as credit,
									he.address_home_id as partner_id
									from hr_provisiones_vaca_line hpvl
									inner join hr_provisiones hpro ON hpro.id = hpvl.provision_id
									inner join hr_payslip_run hpr on hpr.id = hpro.payslip_run_id
									left join hr_contract hc on hc.id = hpvl.contract_id
									left join hr_employee he on he.id = hc.employee_id
									where hpro.company_id = {company}
									and hpr.id = {payslip_run_id}
									and hpro.id = {provision_id}
							) lo
							group by 
							lo.account_id,
							lo.description,
							lo.partner_id 
					""".format(
				company=self.company_id.id,
				payslip_run_id=self.payslip_run_id.id,
				provision_id=self.id)
		else:
			sql_provision = """
							union all
							select 
							lo.account_id,
							lo.description,
							null::integer as analytic_account_id,
        					null::integer as analytic_tag_id,
							sum(lo.debit) as debit,
							sum(lo.credit) as credit,
							null::integer as partner_id
							from (
								select 
									hpro.cts_haber as account_id,
									'Provision de CTS a Pagar'::text as description,
									0::numeric as debit,
									round(hpcl.provisiones_cts::numeric, 2) as credit
									from hr_provisiones_cts_line hpcl
									inner join hr_provisiones hpro ON hpro.id = hpcl.provision_id
									inner join hr_payslip_run hpr on hpr.id = hpro.payslip_run_id
									where hpro.company_id = {company}
									and hpr.id = {payslip_run_id}
									and hpro.id = {provision_id}
								union all
								select 
									hpro.grati_haber as account_id,
									'Provision de Gratificacion a Pagar'::text as description,
									0::numeric as debit,
									round(hpgl.provisiones_grati::numeric, 2) as credit
									from hr_provisiones_grati_line hpgl
									inner join hr_provisiones hpro ON hpro.id = hpgl.provision_id
									inner join hr_payslip_run hpr on hpr.id = hpro.payslip_run_id
									where hpro.company_id = {company}
									and hpr.id = {payslip_run_id}
									and hpro.id = {provision_id}
								union all
								select 
									hpro.boni_haber as account_id,
									'Provision de Gratificacion a Pagar'::text as description,
									0::numeric as debit,
									round(hpgl.boni_grati::numeric, 2) as credit
									from hr_provisiones_grati_line hpgl
									inner join hr_provisiones hpro ON hpro.id = hpgl.provision_id
									inner join hr_payslip_run hpr on hpr.id = hpro.payslip_run_id
									where hpro.company_id = {company}
									and hpr.id = {payslip_run_id}
									and hpro.id = {provision_id}
								union all
								select 
									hpro.vaca_haber as account_id,
									'Provision de Vacaciones a Pagar'::text as description,
									0::numeric as debit,
									round(hpvl.provisiones_vaca::numeric, 2) as credit
									from hr_provisiones_vaca_line hpvl
									inner join hr_provisiones hpro ON hpro.id = hpvl.provision_id
									inner join hr_payslip_run hpr on hpr.id = hpro.payslip_run_id
									where hpro.company_id = {company}
									and hpr.id = {payslip_run_id}
									and hpro.id = {provision_id}
							) lo
							group by 
							lo.account_id,
							lo.description
					""".format(
				company=self.company_id.id,
				payslip_run_id=self.payslip_run_id.id,
				provision_id=self.id)

		sql = """
						SELECT DISTINCT 
							hpro.cts_debe as account_id,
							'Provision de CTS'::text as description,
							aaa.id as analytic_account_id,
							aat.id as analytic_tag_id,
							round(sum(hpcl.provisiones_cts * hadl.percent * 0.01)::numeric, 2) as debit,
							0::numeric as credit,
							null::integer as partner_id
						   FROM hr_provisiones_cts_line hpcl
							INNER JOIN hr_provisiones hpro ON hpro.id = hpcl.provision_id
							INNER JOIN hr_payslip_run hpr on hpr.id = hpro.payslip_run_id
							inner join hr_contract hc on hc.id = hpcl.contract_id 
							inner join hr_analytic_distribution had on had.id = hc.distribution_id
							inner join hr_analytic_distribution_line hadl on hadl.distribution_id = had.id
							inner join account_analytic_account aaa on aaa.id = hadl.analytic_id
							LEFT JOIN (
								select contract_id, min(analytic_tag_id) as analytic_tag_id
								from contract_analytic_tag_rel
								group by contract_id
								) rel ON rel.contract_id = hpcl.contract_id 
							LEFT JOIN account_analytic_tag aat ON aat.id = rel.analytic_tag_id
							where hpro.company_id = {company}
							and hpr.id = {payslip_run_id}
							and hpro.id = {provision_id}
							group by hpro.cts_debe,aaa.id,aat.id,hpro.company_id
						union all 
							SELECT DISTINCT 
							hpro.grati_debe as account_id,
							'Provision de Gratificacion'::text as description,
							aaa.id as analytic_account_id,
							aat.id as analytic_tag_id,
							round(sum(hpgl.provisiones_grati * hadl.percent * 0.01)::numeric, 2) as debit,
							0::numeric as credit,
							null::integer as partner_id
						   FROM hr_provisiones_grati_line hpgl
							INNER JOIN hr_provisiones hpro ON hpro.id = hpgl.provision_id
							INNER JOIN hr_payslip_run hpr on hpr.id = hpro.payslip_run_id
							inner join hr_contract hc on hc.id = hpgl.contract_id 
							inner join hr_analytic_distribution had on had.id = hc.distribution_id
							inner join hr_analytic_distribution_line hadl on hadl.distribution_id = had.id
							inner join account_analytic_account aaa on aaa.id = hadl.analytic_id
							LEFT JOIN (
								select contract_id, min(analytic_tag_id) as analytic_tag_id
								from contract_analytic_tag_rel
								group by contract_id
								) rel ON rel.contract_id = hpgl.contract_id 
							LEFT JOIN account_analytic_tag aat ON aat.id = rel.analytic_tag_id
							where hpro.company_id = {company}
							and hpr.id = {payslip_run_id}
							and hpro.id = {provision_id}
							group by hpro.grati_debe,aaa.id,aat.id,hpro.company_id
						union all 
							SELECT DISTINCT 
							hpro.boni_debe as account_id,
							'Provision del Bono Extraordinario'::text as description,
							aaa.id as analytic_account_id,
							aat.id as analytic_tag_id,
							round(sum(hpgl.boni_grati * hadl.percent * 0.01)::numeric, 2) as debit,
							0::numeric as credit,
							null::integer as partner_id
						   FROM hr_provisiones_grati_line hpgl
							INNER JOIN hr_provisiones hpro ON hpro.id = hpgl.provision_id
							INNER JOIN hr_payslip_run hpr on hpr.id = hpro.payslip_run_id
							inner join hr_contract hc on hc.id = hpgl.contract_id 
							inner join hr_analytic_distribution had on had.id = hc.distribution_id
							inner join hr_analytic_distribution_line hadl on hadl.distribution_id = had.id
							inner join account_analytic_account aaa on aaa.id = hadl.analytic_id
							LEFT JOIN (
								select contract_id, min(analytic_tag_id) as analytic_tag_id
								from contract_analytic_tag_rel
								group by contract_id
								) rel ON rel.contract_id = hpgl.contract_id 
							LEFT JOIN account_analytic_tag aat ON aat.id = rel.analytic_tag_id
							where hpro.company_id = {company}
							and hpr.id = {payslip_run_id}
							and hpro.id = {provision_id}
							group by hpro.boni_debe,aaa.id,aat.id,hpro.company_id
						union all 
							SELECT DISTINCT 
							hpro.vaca_debe as account_id,
							'Provision de Vacaciones'::text as description,
							aaa.id as analytic_account_id,
							aat.id as analytic_tag_id,
							round(sum(hpvl.provisiones_vaca * hadl.percent * 0.01)::numeric, 2) as debit,
							0::numeric as credit,
							null::integer as partner_id
						   FROM hr_provisiones_vaca_line hpvl
							INNER JOIN hr_provisiones hpro ON hpro.id = hpvl.provision_id
							INNER JOIN hr_payslip_run hpr on hpr.id = hpro.payslip_run_id
							inner join hr_contract hc on hc.id = hpvl.contract_id 
							inner join hr_analytic_distribution had on had.id = hc.distribution_id
							inner join hr_analytic_distribution_line hadl on hadl.distribution_id = had.id
							inner join account_analytic_account aaa on aaa.id = hadl.analytic_id
							LEFT JOIN (
								select contract_id, min(analytic_tag_id) as analytic_tag_id
								from contract_analytic_tag_rel
								group by contract_id
								) rel ON rel.contract_id = hpvl.contract_id 
							LEFT JOIN account_analytic_tag aat ON aat.id = rel.analytic_tag_id
							where hpro.company_id = {company}
							and hpr.id = {payslip_run_id}
							and hpro.id = {provision_id}
							group by hpro.vaca_debe,aaa.id,aat.id,hpro.company_id
						{sql_provision}
						""".format(
			company=self.company_id.id,
			payslip_run_id=self.payslip_run_id.id,
			provision_id=self.id,
			sql_provision=sql_provision
		)
		# print("sql",sql)
		self._cr.execute(sql)
		move_lines = self._cr.dictfetchall()
		# print("move_lines",move_lines)
		return move_lines