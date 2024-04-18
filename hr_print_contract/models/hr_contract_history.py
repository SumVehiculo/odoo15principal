# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
from collections import defaultdict

class ContractHistory(models.Model):
    _inherit = 'hr.contract.history'

    state = fields.Selection([
        ('draft', 'Nuevo'),
        ('open', 'En proceso'),
        ('expire', 'Por vencer'),
        ('close', 'Vencido'),
        ('cancel', 'Cancelado')
    ], string='Estado', readonly=True)

    @api.model
    def _get_fields(self):
        return ','.join('contract.%s' % name for name, field in self._fields.items()
                        if field.store
                        and field.type not in ['many2many', 'one2many', 'related']
                        and field.name not in ['id','state', 'contract_id', 'employee_id', 'date_hired', 'is_under_contract', 'active_employee'])

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        # Reference contract is the one with the latest start_date.
        self.env.cr.execute("""CREATE or REPLACE VIEW %s AS (
            WITH contract_information AS (
                SELECT DISTINCT employee_id,
                                company_id,
                                FIRST_VALUE(id) OVER w_partition AS id,
                                MAX(CASE
                                    WHEN state='open' THEN 1
                                    WHEN state='draft' AND kanban_state='done' THEN 1
                                    ELSE 0 END) OVER w_partition AS is_under_contract
                FROM   hr_contract AS contract
                WHERE  contract.state <> 'cancel'
                AND contract.active = true
                WINDOW w_partition AS (
                    PARTITION BY contract.employee_id
                    ORDER BY
                        CASE
                            WHEN contract.state = 'open' THEN 0
                            WHEN contract.state = 'draft' THEN 1
                            WHEN contract.state = 'close' THEN 2
                            ELSE 3 END,
                        contract.date_start DESC
                    RANGE BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
                )
            )
            SELECT     employee.id AS id,
                       employee.id AS employee_id,
                       employee.active AS active_employee,
                       contract.id AS contract_id,
                       contract_information.is_under_contract::bool AS is_under_contract,
                       employee.first_contract_date AS date_hired,
                       CASE
                            WHEN contract.state = 'open' AND contract.date_end is not null THEN (
                                 CASE WHEN
                                 abs(contract.date_end - current_date) <= 30 THEN 'expire' ELSE 'open' END)
                            WHEN contract.state = 'open' AND contract.date_end is null THEN 'open'
                            WHEN contract.state = 'draft' THEN 'draft'
                            WHEN contract.state = 'close' THEN 'close'
                            WHEN contract.state = 'cancel' THEN 'cancel'
                            END as state,
                       %s
            FROM       hr_contract AS contract
            INNER JOIN contract_information ON contract.id = contract_information.id
            RIGHT JOIN hr_employee AS employee
                ON  contract_information.employee_id = employee.id
                AND contract.company_id = employee.company_id
            WHERE   employee.employee_type IN ('employee', 'student', 'trainee')
        )""" % (self._table, self._get_fields()))