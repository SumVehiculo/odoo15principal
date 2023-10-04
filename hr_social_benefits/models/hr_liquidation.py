# -*- coding:utf-8 -*-
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError
from datetime import *
from calendar import *
from dateutil.relativedelta import relativedelta
import base64

class HrLiquidation(models.Model):
    _name = 'hr.liquidation'
    _description = 'Liquidation'
    _rec_name = 'payslip_run_id'

    name = fields.Char()
    company_id = fields.Many2one('res.company', string='Compañia', default=lambda self: self.env.company.id, required=True, states={'exported': [('readonly', True)]})
    fiscal_year_id = fields.Many2one('account.fiscal.year', string='Año Fiscal', required=True, states={'exported': [('readonly', True)]})
    with_bonus = fields.Boolean(string='Bono Extraordinario', default=False, states={'exported': [('readonly', True)]})
    months_and_days = fields.Boolean(string='Calcular Dias Grati.', default=False, states={'exported': [('readonly', True)]})
    exchange_type = fields.Float(string='Tipo de Cambio', default=1, states={'exported': [('readonly', True)]})
    gratification_type = fields.Selection([('07', 'Gratificacion Fiestas Patrias'),
                                           ('12', 'Gratificacion Navidad')], string='Tipo Gratificacion', required=True, states={'exported': [('readonly', True)]})
    cts_type = fields.Selection([('11', 'CTS Mayo - Octubre'),
                                 ('05', 'CTS Noviembre - Abril')], string='Tipo CTS', required=True, states={'exported': [('readonly', True)]})
    payslip_run_id = fields.Many2one('hr.payslip.run', string='Periodo', required=True, states={'exported': [('readonly', True)]})
    gratification_line_ids = fields.One2many('hr.gratification.line', 'liquidation_id', states={'exported': [('readonly', True)]}, string='Calculo de Gratificaciones Truncas')
    cts_line_ids = fields.One2many('hr.cts.line', 'liquidation_id', states={'exported': [('readonly', True)]}, string='Calculo de CTS Trunca')
    vacation_line_ids = fields.One2many('hr.liquidation.vacation.line', 'liquidation_id', states={'exported': [('readonly', True)]}, string='Calculo de Vacaciones Truncas')
    # compensation_line_ids = fields.One2many('hr.compensation.line', 'liquidation_id', states={'exported': [('readonly', True)]})
    employee_ids = fields.One2many('hr.employee', 'liquidation_id', string='Empleados')
    employee_count = fields.Integer(compute='_compute_employee_count')
    state = fields.Selection([('draft', 'Borrador'), ('exported', 'Exportado')], default='draft', string='Estado')

    liq_ext_concept_ids = fields.One2many('hr.liquidation.extra_concepts', 'liquidation_id',states={'exported': [('readonly', True)]},)

    def _compute_employee_count(self):
        for record in self:
            record.employee_count = len(self.employee_ids)

    def turn_draft(self):
        self.state = 'draft'

    def compute_liquidation_all(self):
        self.gratification_line_ids.compute_grati_line()
        self.cts_line_ids.compute_cts_line()
        self.vacation_line_ids.compute_vacation_line()
        return self.env['popup.it'].get_message('Se Recalculo exitosamente')

    def export_liquidation(self):
        MainParameter = self.env['hr.main.parameter'].get_main_parameter()
        MainParameter.check_liquidation_values()
        Lot = self.payslip_run_id
        for line in self.gratification_line_ids:
            Slip = Lot.slip_ids.filtered(lambda slip: slip.employee_id == line.employee_id)
            grat_line = Slip.input_line_ids.filtered(lambda inp: inp.input_type_id == MainParameter.truncated_gratification_input_id)
            bonus_line = Slip.input_line_ids.filtered(lambda inp: inp.input_type_id == MainParameter.truncated_bonus_nine_input_id)
            grat_line.amount = line.total_grat
            bonus_line.amount = line.bonus_essalud
        for line in self.cts_line_ids:
            Slip = Lot.slip_ids.filtered(lambda slip: slip.employee_id == line.employee_id)
            cts_line = Slip.input_line_ids.filtered(lambda inp: inp.input_type_id == MainParameter.truncated_cts_input_id)
            cts_line.amount = line.total_cts
        for line in self.vacation_line_ids:
            Slip = Lot.slip_ids.filtered(lambda slip: slip.employee_id == line.employee_id)
            vac_line = Slip.input_line_ids.filtered(lambda inp: inp.input_type_id == MainParameter.vacation_input_id)
            trunc_vac_line = Slip.input_line_ids.filtered(lambda inp: inp.input_type_id == MainParameter.truncated_vacation_input_id)
            vac_line.amount = line.accrued_vacation
            trunc_vac_line.amount = line.truncated_vacation

        for line in self.liq_ext_concept_ids:
            Slip = Lot.slip_ids.filtered(lambda slip: slip.employee_id == line.employee_id)
            for line_input in line.concept_ids:
                for line in line_input.conceptos_lines:
                    extra_line = Slip.input_line_ids.filtered(lambda inp: inp.input_type_id == line.name_input_id)
                    extra_line.amount = line.amount
                    # print("codigo",extra_line.code)

        self.state = 'exported'
        return self.env['popup.it'].get_message('Se exporto exitosamente')

    def get_liquidation_employees(self):
        self.ensure_one()
        self.employee_ids.write({'liquidation_id': self.id})
        return {
            "type": "ir.actions.act_window",
            "res_model": "hr.employee",
            "views": [[False, "tree"]],
            "domain": [['id', 'in', self.employee_ids.ids]],
            "name": "Empleados",
        }

    @api.onchange('fiscal_year_id', 'payslip_run_id')
    def _get_name(self):
        for record in self:
            if record.fiscal_year_id and record.payslip_run_id:
                record.name = 'Liquidacion {0}'.format(record.payslip_run_id.name)

    @api.onchange('payslip_run_id')
    def _get_type(self):
        for record in self:
            if record.payslip_run_id:
                month = record.payslip_run_id.date_start.month
                if record.payslip_run_id and month > 6:
                    record.gratification_type = '12'
                else:
                    record.gratification_type = '07'
                if record.payslip_run_id and ((10 < month and month <= 12) or (1 <= month and month < 5)):
                    record.cts_type = '05'
                else:
                    record.cts_type = '11'

    def get_date_limit_from(self, date_limit_to):
        #####Logic to get the last 6 months from cessation_date 'cause all bonifications need this months to average the amount#####
        last_day = monthrange(date_limit_to.year, date_limit_to.month)[1]
        if last_day == date_limit_to.day:
            date_limit_from = date_limit_to - relativedelta(months=+6)
            limit_last_day = monthrange(date_limit_from.year, date_limit_from.month)[1]
            if limit_last_day == date_limit_from.day:
                date_limit_from += timedelta(days=1)
            else:
                result = limit_last_day - date_limit_from.day + 1
                date_limit_from += timedelta(days=result)
        else:
            date_limit_from = date_limit_to - relativedelta(months=+6)
            date_limit_from = date(date_limit_from.year, date_limit_from.month, 1)
        return date_limit_from

    def get_vacation_lines(self):
        year = int(self.fiscal_year_id.name)
        MainParameter = self.env['hr.main.parameter'].get_main_parameter()
        ReportBase = self.env['report.base']
        MonthLot = self.payslip_run_id
        Employees = MonthLot.slip_ids.filtered(lambda slip: slip.contract_id.labor_regime in ['general', 'small','micro'] and
                                                            slip.contract_id.situation_id.code == '0' and
                                                            slip.date_from <= slip.contract_id.date_end and
                                                            slip.date_to >= slip.contract_id.date_end and
                                                            not slip.contract_id.less_than_four).mapped('employee_id')

        for Employee in Employees:
            # print('empleados',Employee.name)
            bonus_months = months = days = lacks = 0
            Commissions = Bonus = ExtraHours = self.env['hr.payslip.line']
            # print('comisiones',Commissions)
            MonthSlip = MonthLot.slip_ids.filtered(lambda slip: slip.employee_id == Employee)
            # print('MonthSlip',MonthSlip)
            admission_date = self.env['hr.contract'].get_first_contract(Employee, MonthSlip.contract_id).date_start
            # print('admission_date',admission_date)
            compute_date = date(year, admission_date.month, admission_date.day)
            # print("date",year, admission_date.month, admission_date.day)
            # print('compute_date',compute_date)
            # wage = MonthSlip.line_ids.filtered(lambda line: line.salary_rule_id == MainParameter.basic_sr_id).total
            # wage= MonthSlip.contract_id.wage
            wage= MonthSlip.wage
            # print('wage',wage)
            household_allowance = MonthSlip.line_ids.filtered(lambda line: line.salary_rule_id == MainParameter.household_allowance_sr_id).total
            # print('household_allowance',household_allowance)
            compute_payslip_date = date(compute_date.year, compute_date.month, 1)
            # print('compute_payslip_date',compute_payslip_date)
            # print('MonthSlip.date_to',MonthSlip.date_to)
            Lots = self.env['hr.payslip.run'].search([('date_start', '>=', compute_payslip_date),
                                                      ('date_end', '<=', MonthSlip.date_to)])
            # print('Lots primero',Lots)
            for Lot in Lots:
                # print('Lot',Lot.name)
                EmployeeSlips = Lot.slip_ids.filtered(lambda slip: slip.employee_id == Employee)
                SalaryRules = EmployeeSlips.mapped('line_ids')
                WorkedDays = EmployeeSlips.mapped('worked_days_line_ids')
                WorkingWD =	sum(WorkedDays.filtered(lambda line: line.wd_type_id in MainParameter.working_wd_ids).mapped('number_of_days'))
                if WorkingWD >= 30:
                    months += 1
                else:
                    days += WorkingWD

                LackWD = sum(WorkedDays.filtered(lambda line: line.wd_type_id == MainParameter.lack_wd_id).mapped('number_of_days'))
                lacks += LackWD
            # print("lacks",lacks)
            # print("meses",months)
            # print("days",days)
            date_limit_to = MonthSlip.contract_id.date_end
            # print('date_limit_to',date_limit_to)
            date_limit_from = self.get_date_limit_from(date_limit_to)
            # print('date_limit_from',date_limit_from)
            Lots = self.env['hr.payslip.run'].search([('date_start', '>=', date_limit_from),
                                                      ('date_end', '<=', date_limit_to)])
            # print('Lots',Lots)
            bonus_months = len(Lots.mapped('slip_ids').filtered(lambda slip: slip.employee_id == Employee))
            for Lot in Lots:
                # print('Lot',Lot.name)
                EmployeeSlips = Lot.slip_ids.filtered(lambda slip: slip.employee_id == Employee)
                SalaryRules = EmployeeSlips.mapped('line_ids')
                Commissions += SalaryRules.filtered(lambda line: line.salary_rule_id in MainParameter.commission_sr_ids and line.total > 0)
                Bonus += SalaryRules.filtered(lambda line: line.salary_rule_id in MainParameter.bonus_sr_ids and line.total > 0)
                ExtraHours += SalaryRules.filtered(lambda line: line.salary_rule_id == MainParameter.extra_hours_sr_id and line.total > 0)
            # 	months += 1
            # print("month",months)
            commission = MainParameter.calculate_bonus(admission_date, date_limit_from, bonus_months, Commissions)
            bonus = MainParameter.calculate_bonus(admission_date, date_limit_from, bonus_months, Bonus)
            extra_hours = MainParameter.calculate_bonus(admission_date, date_limit_from, bonus_months, ExtraHours)
            computable_remuneration = wage + household_allowance + commission + bonus + extra_hours
            medical_days, excess_medical_rest = MainParameter.calculate_excess_medical_rest(year, Employee)
            # print('computable_remuneration',computable_remuneration)
            days = days + medical_days
            # print('days',days)
            if days >= 30:
                days, months = MainParameter.get_months_of_30_days(days, months)
            # print('days: ',days,'    months:',months)
            amount_per_month = computable_remuneration/12 if MonthSlip.contract_id.labor_regime == 'general' else computable_remuneration/24
            # print('amount_per_month',amount_per_month)
            amount_per_day = amount_per_month/30
            # print('amount_per_day',amount_per_day)
            amount_per_lack = amount_per_day * lacks
            vacation_per_month = ReportBase.custom_round(amount_per_month * months, 2)
            # print('vacation_per_month',vacation_per_month)
            vacation_per_day = ReportBase.custom_round(amount_per_day * days, 2)
            # print('vacation_per_day',vacation_per_day)
            truncated_vacation = ReportBase.custom_round((vacation_per_month + vacation_per_day) - amount_per_lack, 2)
            total_vacation = truncated_vacation
            # print('vacacion trunca',total_vacation)
            membership = MonthSlip.contract_id.membership_id
            onp = afp_jub = afp_si = afp_mixed_com = afp_fixed_com = 0
            if membership.is_afp:
                afp_jub = ReportBase.custom_round(membership.retirement_fund/100 * total_vacation, 2)
                afp_si = ReportBase.custom_round(membership.prima_insurance/100 * total_vacation, 2)
                if MonthSlip.contract_id.commision_type == 'mixed':
                    afp_mixed_com = ReportBase.custom_round(membership.mixed_commision/100 * total_vacation, 2)
                    afp_fixed_com =0
                elif MonthSlip.contract_id.commision_type == 'flow':
                    afp_fixed_com = ReportBase.custom_round(membership.fixed_commision /100 * total_vacation, 2)
                    afp_mixed_com =0
            else:
                onp = ReportBase.custom_round(membership.retirement_fund/100 * total_vacation, 2)
            total = ReportBase.custom_round(total_vacation - afp_jub - afp_si - afp_mixed_com - afp_fixed_com - onp, 2)
            vals = {
                'liquidation_id': self.id,
                'employee_id': Employee.id,
                'contract_id': MonthSlip.contract_id.id,
                'distribution_id': MonthSlip.contract_id.distribution_id.name,
                'admission_date': admission_date,
                'compute_date': compute_date,
                'cessation_date': MonthSlip.contract_id.date_end,
                'membership_id': membership.id,
                'months': months,
                'days': days,
                'lacks': lacks,
                'wage': wage,
                'household_allowance': household_allowance,
                'commission': commission,
                'bonus': bonus,
                'extra_hours': extra_hours,
                'computable_remuneration': computable_remuneration,
                'amount_per_month': amount_per_month,
                'amount_per_day': amount_per_day,
                'vacation_per_month': vacation_per_month,
                'vacation_per_day': vacation_per_day,
                'truncated_vacation': truncated_vacation,
                'total_vacation': total_vacation,
                'onp': onp,
                'afp_jub': afp_jub,
                'afp_si': afp_si,
                'afp_mixed_com': afp_mixed_com,
                'afp_fixed_com': afp_fixed_com,
                'total': total
            }
            self.env['hr.liquidation.vacation.line'].create(vals)

    def get_extra_concepts_lines(self):
        MonthLot = self.payslip_run_id
        Employees = MonthLot.slip_ids.filtered(lambda slip: slip.contract_id.labor_regime in ['general', 'small'] and
                                                            slip.contract_id.situation_id.code == '0' and
                                                            slip.date_from <= slip.contract_id.date_end and
                                                            slip.date_to >= slip.contract_id.date_end).mapped(
            'employee_id')
        self.employee_ids = [(6, 0, Employees.ids)]
        Employees = MonthLot.slip_ids.filtered(lambda slip: slip.contract_id.labor_regime in ['general', 'small'] and
                                                            slip.contract_id.situation_id.code == '0' and
                                                            slip.date_from <= slip.contract_id.date_end and
                                                            slip.date_to >= slip.contract_id.date_end and
                                                            not slip.contract_id.less_than_four).mapped('employee_id')
        for Employee in Employees:
            Contract = MonthLot.mapped('slip_ids').filtered(lambda slip: slip.employee_id == Employee).contract_id
            admission_date = self.env['hr.contract'].get_first_contract(Employee, Contract).date_start
            vals = {'liquidation_id': self.id,
                    'employee_id': Employee.id,
                    'contract_id': Contract.id,
                    'admission_date': admission_date,
                    'cessation_date': Contract.date_end}
            self.env['hr.liquidation.extra_concepts'].create(vals)

    def get_liquidation(self):
        # self.gratification_line_ids.unlink()
        # self.cts_line_ids.unlink()
        # self.vacation_line_ids.unlink()
        # self.compensation_line_ids.unlink()
        self.env['hr.gratification.line'].search([('liquidation_id','=',self.id),('preserve_record','=',False)]).unlink()
        self.env['hr.cts.line'].search([('liquidation_id','=',self.id),('preserve_record','=',False)]).unlink()
        self.env['hr.liquidation.vacation.line'].search([('liquidation_id','=',self.id),('preserve_record','=',False)]).unlink()
        # self.env['hr.compensation.line'].search([('liquidation_id','=',self.id),('preserve_record','=',False)]).unlink()
        self.env['hr.liquidation.extra_concepts'].search([('liquidation_id','=',self.id),('preserve_record','=',False)]).unlink()
        # self.liq_ext_concept_ids.unlink()
        MainParameter = self.env['hr.main.parameter']
        MainParameter.compute_benefits(self, self.gratification_type, liquidation=self)
        MainParameter.compute_benefits(self, self.cts_type, liquidation=self)
        self.get_vacation_lines()
        self.get_extra_concepts_lines()

        # for emp in self.employee_ids:
        #     self.env['hr.liquidation.extra_concepts'].create({
        #         'liquidation_id': self.id,
        #         'employee_id': emp.id,
        #     })

        preservados = self.env['hr.gratification.line'].search(
            [('liquidation_id', '=', self.id), ('preserve_record', '=', True)])
        empleados_pre = []
        for j in preservados:
            if j.employee_id.id not in empleados_pre:
                empleados_pre.append(j.employee_id.id)
        eliminar = []
        for l in self.gratification_line_ids:
            if l.employee_id.id in empleados_pre:
                if l.preserve_record == False:
                    eliminar.append(l)
        for l in eliminar:
            l.unlink()

        preservados = self.env['hr.cts.line'].search([('liquidation_id', '=', self.id), ('preserve_record', '=', True)])
        empleados_pre = []
        for j in preservados:
            if j.employee_id.id not in empleados_pre:
                empleados_pre.append(j.employee_id.id)
        eliminar = []
        for l in self.cts_line_ids:
            if l.employee_id.id in empleados_pre:
                if l.preserve_record == False:
                    eliminar.append(l)
        for l in eliminar:
            l.unlink()

        preservados = self.env['hr.liquidation.vacation.line'].search(
            [('liquidation_id', '=', self.id), ('preserve_record', '=', True)])
        empleados_pre = []
        for j in preservados:
            if j.employee_id.id not in empleados_pre:
                empleados_pre.append(j.employee_id.id)
        eliminar = []
        for l in self.vacation_line_ids:
            if l.employee_id.id in empleados_pre:
                if l.preserve_record == False:
                    eliminar.append(l)
        for l in eliminar:
            l.unlink()

        preservados = self.env['hr.liquidation.extra_concepts'].search(
            [('liquidation_id', '=', self.id), ('preserve_record', '=', True)])
        empleados_pre = []
        for j in preservados:
            if j.employee_id.id not in empleados_pre:
                empleados_pre.append(j.employee_id.id)
        eliminar = []
        for l in self.liq_ext_concept_ids:
            if l.employee_id.id in empleados_pre:
                if l.preserve_record == False:
                    eliminar.append(l)
        for l in eliminar:
            l.unlink()

        return self.env['popup.it'].get_message('Se calculo exitosamente')

    def get_excel_liquidation(self):
        import io
        from xlsxwriter.workbook import Workbook
        MainParameter = self.env['hr.main.parameter'].get_main_parameter()
        route = MainParameter.dir_create_file
        gratification_type = dict(self._fields['gratification_type'].selection).get(self.gratification_type)

        if not route:
            raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Nomina para su Compañía')
        doc_name = '%s %s.xlsx' % ('Liquidacion', self.payslip_run_id.name.name)
        workbook = Workbook(route + doc_name)

        self.env['hr.gratification'].get_gratification_sheet(workbook, self.gratification_line_ids, liquidation=True)
        self.env['hr.cts'].get_cts_sheet(workbook, self.cts_line_ids, liquidation=True)
        self.env['hr.liquidation'].get_vacation_sheet(workbook, self.vacation_line_ids)
        self.env['hr.liquidation'].get_extra_concepts_sheet(workbook, self.liq_ext_concept_ids)
        workbook.close()
        f = open(route + doc_name, 'rb')
        return self.env['popup.it'].get_file(doc_name, base64.encodebytes(b''.join(f.readlines())))

    def get_vacation_sheet(self, workbook, lines):
        ReportBase = self.env['report.base']
        workbook, formats = ReportBase.get_formats(workbook)

        import importlib
        import sys
        importlib.reload(sys)

        worksheet = workbook.add_worksheet('VACACIONES')
        worksheet.set_tab_color('yellow')

        #### I'm separating this array of headers 'cause i need a dynamic limiter to set the totals at the end of the printing, i will use the HEADER variable to get the lenght and this will be my limiter'
        HEADERS = ['NRO. DOCUMENTO', 'APELLIDO MATERNO', 'APELLIDO PATERNO', 'NOMBRES', 'FECHA INGRESO', 'FECHA DE COMPUTO', 'FECHA DE CESE', 'AFILIACION','DISTRIBUCION ANALITICA',
                   'MES', 'DIAS', 'FALTAS']
        HEADERS_WITH_TOTAL = ['SUELDO', 'ASIGNACION FAMILIAR', 'PROMEDIO COMISION', 'PROMEDIO BONIFICACION', 'PROMEDIO HRS EXTRAS', 'REMUNERACION COMPUTABLE',
                              'MONTO POR MES', 'MONTO POR DIA', 'VAC. POR MESES', 'VAC. POR DIAS', 'VAC. ADELANTADAS', 'VAC. DEVENGADAS', 'VAC. TRUNCAS',
                              'TOTAL VAC.', 'ONP', 'AFP JUB', 'AFP SI', 'AFP COM. MIXTA', 'AFP COM. FIJA', 'NETO TOTAL']
        worksheet = ReportBase.get_headers(worksheet, HEADERS + HEADERS_WITH_TOTAL, 0, 0, formats['boldbord'])
        x, y = 1, 0
        totals = [0] * len(HEADERS_WITH_TOTAL)
        limiter = len(HEADERS)
        for line in lines:
            worksheet.write(x, 0, line.identification_id or '', formats['especial1'])
            worksheet.write(x, 1, line.last_name or '', formats['especial1'])
            worksheet.write(x, 2, line.m_last_name or '', formats['especial1'])
            worksheet.write(x, 3, line.names or '', formats['especial1'])
            worksheet.write(x, 4, line.admission_date or '', formats['reverse_dateformat'])
            worksheet.write(x, 5, line.compute_date or '', formats['reverse_dateformat'])
            worksheet.write(x, 6, line.cessation_date or '', formats['reverse_dateformat'])
            worksheet.write(x, 7, line.membership_id.name or '', formats['especial1'])
            worksheet.write(x, 8, line.distribution_id or '', formats['especial1'])
            worksheet.write(x, 9, line.months or 0, formats['number'])
            worksheet.write(x, 10, line.days or 0, formats['number'])
            worksheet.write(x, 11, line.lacks or 0, formats['number'])
            worksheet.write(x, 12, line.wage or 0, formats['numberdos'])
            worksheet.write(x, 13, line.household_allowance or 0, formats['numberdos'])
            worksheet.write(x, 14, line.commission or 0, formats['numberdos'])
            worksheet.write(x, 15, line.bonus or 0, formats['numberdos'])
            worksheet.write(x, 16, line.extra_hours or 0, formats['numberdos'])
            worksheet.write(x, 17, line.computable_remuneration or 0, formats['numberdos'])
            worksheet.write(x, 18, line.amount_per_month or 0, formats['numberdos'])
            worksheet.write(x, 19, line.amount_per_day or 0, formats['numberdos'])
            worksheet.write(x, 20, line.vacation_per_month or 0, formats['numberdos'])
            worksheet.write(x, 21, line.vacation_per_day or 0, formats['numberdos'])
            worksheet.write(x, 22, line.advanced_vacation or 0, formats['numberdos'])
            worksheet.write(x, 23, line.accrued_vacation or 0, formats['numberdos'])
            worksheet.write(x, 24, line.truncated_vacation or 0, formats['numberdos'])
            worksheet.write(x, 25, line.total_vacation or 0, formats['numberdos'])
            worksheet.write(x, 26, line.onp or 0, formats['numberdos'])
            worksheet.write(x, 27, line.afp_jub or 0, formats['numberdos'])
            worksheet.write(x, 28, line.afp_si or 0, formats['numberdos'])
            worksheet.write(x, 29, line.afp_mixed_com or 0, formats['numberdos'])
            worksheet.write(x, 30, line.afp_fixed_com or 0, formats['numberdos'])
            worksheet.write(x, 31, line.total or 0, formats['numberdos'])

            totals[0] += line.wage
            totals[1] += line.household_allowance
            totals[2] += line.commission
            totals[3] += line.bonus
            totals[4] += line.extra_hours
            totals[5] += line.computable_remuneration
            totals[6] += line.amount_per_month
            totals[7] += line.amount_per_day
            totals[8] += line.vacation_per_month
            totals[9] += line.vacation_per_day
            totals[10] += line.advanced_vacation
            totals[11] += line.accrued_vacation
            totals[12] += line.truncated_vacation
            totals[13] += line.total_vacation
            totals[14] += line.onp
            totals[15] += line.afp_jub
            totals[16] += line.afp_si
            totals[17] += line.afp_mixed_com
            totals[18] += line.afp_fixed_com
            totals[19] += line.total

            x += 1
        x += 1
        for total in totals:
            worksheet.write(x, limiter, total, formats['numbertotal'])
            limiter += 1
        widths = [13, 13, 13, 20, 10, 11,11, 15, 15, 5, 5,
                  8, 11, 16, 13, 16, 14, 16, 11, 11, 10,
                  10, 15, 15, 15, 9, 9, 9, 8, 10, 10,
                  10]
        worksheet = ReportBase.resize_cells(worksheet, widths)

    def get_extra_concepts_sheet(self, workbook, lines):
        ReportBase = self.env['report.base']
        workbook, formats = ReportBase.get_formats(workbook)

        import importlib
        import sys
        importlib.reload(sys)

        worksheet = workbook.add_worksheet('CONCEPTOS EXTRAS')
        worksheet.set_tab_color('orange')

        #### I'm separating this array of headers 'cause i need a dynamic limiter to set the totals at the end of the printing, i will use the HEADER variable to get the lenght and this will be my limiter'
        HEADERS = ['NRO. DOCUMENTO', 'APELLIDO MATERNO', 'APELLIDO PATERNO', 'NOMBRES', 'FECHA INGRESO',
                   'FECHA DE CESE']
        HEADERS_WITH_TOTAL = ['TOTAL INGRESO', 'TOTAL DESCUENTO']
        worksheet = ReportBase.get_headers(worksheet, HEADERS + HEADERS_WITH_TOTAL, 0, 0, formats['boldbord'])
        x, y = 1, 0
        totals = [0] * len(HEADERS_WITH_TOTAL)
        limiter = len(HEADERS)
        for line in lines:
            worksheet.write(x, 0, line.identification_id or '', formats['especial1'])
            worksheet.write(x, 1, line.employee_id.last_name or '', formats['especial1'])
            worksheet.write(x, 2, line.employee_id.m_last_name or '', formats['especial1'])
            worksheet.write(x, 3, line.employee_id.names or '', formats['especial1'])
            worksheet.write(x, 4, line.admission_date or '', formats['reverse_dateformat'])
            worksheet.write(x, 5, line.cessation_date or '', formats['reverse_dateformat'])
            worksheet.write(x, 6, line.income or 0, formats['numberdos'])
            worksheet.write(x, 7, line.expenses or 0, formats['numberdos'])

            totals[0] += line.income
            totals[1] += line.expenses

            x += 1
        x += 1
        for total in totals:
            worksheet.write(x, limiter, total, formats['numbertotal'])
            limiter += 1
        widths = [14, 14, 14, 20, 14, 14, 14, 14]
        worksheet = ReportBase.resize_cells(worksheet, widths)

class HrLiquidationVacationLine(models.Model):
    _name = 'hr.liquidation.vacation.line'
    _description = 'Liquidation Vacation Line'

    liquidation_id = fields.Many2one('hr.liquidation', ondelete='cascade')
    employee_id = fields.Many2one('hr.employee', string='Empleado')
    contract_id = fields.Many2one('hr.contract', string='Contrato')
    identification_id = fields.Char(related='employee_id.identification_id', string='Nro Documento')
    last_name = fields.Char(related='employee_id.last_name', string='Apellido Paterno')
    m_last_name = fields.Char(related='employee_id.m_last_name', string='Apellido Materno')
    names = fields.Char(related='employee_id.names', string='Nombres')
    admission_date = fields.Date(string='Fecha de Ingreso')
    compute_date = fields.Date(string='Fecha de Computo')
    cessation_date = fields.Date(string='Fecha de Cese')
    membership_id = fields.Many2one(related='contract_id.membership_id', string='Afiliacion')
    distribution_id = fields.Char(string='Distribucion Analitica')
    months = fields.Integer(string='Meses')
    days = fields.Integer(string='Dias')
    lacks = fields.Integer(string='Faltas')
    wage = fields.Float(string='Sueldo')
    household_allowance = fields.Float(string='Asignacion Familiar')
    commission = fields.Float(string='Prom. Comision')
    bonus = fields.Float(string='Prom. Bonificacion')
    extra_hours = fields.Float(string='Prom. Horas Extras')
    computable_remuneration = fields.Float(string='Remuneracion Computable')
    amount_per_month = fields.Float(string='Monto por Mes')
    amount_per_day = fields.Float(string='Monto por Dia')
    vacation_per_month = fields.Float(string='Vac. por Mes')
    vacation_per_day = fields.Float(string='Vac. por Dia')
    advanced_vacation = fields.Float(string='(-) Vac. Adelantadas')
    accrued_vacation = fields.Float(string='(+) Vac. Devengadas')
    truncated_vacation = fields.Float(string='Vac. Truncas')
    total_vacation = fields.Float(string='Total Vacaciones')
    onp = fields.Float(string='(-) ONP')
    afp_jub = fields.Float(string='(-) AFP JUB')
    afp_si = fields.Float(string='(-) AFP SI')
    afp_mixed_com = fields.Float(string='(-) AFP COM. MIXTA')
    afp_fixed_com = fields.Float(string='(-) AFP COM. FIJA')
    total = fields.Float(string='Neto Total')

    preserve_record = fields.Boolean('No Recalcular')

    def compute_vacation_line(self):
        ReportBase = self.env['report.base']
        self.env['hr.liquidation.vacation.line'].search([('liquidation_id', '=', None), ('id', 'not in', self.ids)]).unlink()

        for record in self:
            record.computable_remuneration = record.wage + record.household_allowance + record.commission + record.bonus + record.extra_hours
            record.amount_per_month = record.computable_remuneration/12 if record.contract_id.labor_regime == 'general' else record.computable_remuneration/24
            record.amount_per_day = record.amount_per_month/30
            amount_per_lack = record.amount_per_day * record.lacks
            record.vacation_per_month = ReportBase.custom_round(record.amount_per_month * record.months, 2)
            record.vacation_per_day = ReportBase.custom_round(record.amount_per_day * record.days, 2)
            record.truncated_vacation = ReportBase.custom_round((record.vacation_per_month + record.vacation_per_day) - amount_per_lack, 2)
            record.total_vacation = record.accrued_vacation + record.truncated_vacation - record.advanced_vacation
            membership = record.contract_id.membership_id
            onp = afp_jub = afp_si = afp_mixed_com= afp_fixed_com= 0
            if membership.is_afp:
                afp_jub = ReportBase.custom_round(membership.retirement_fund/100 * record.total_vacation, 2)
                if record.accrued_vacation>=membership.insurable_remuneration:
                    afp_si = ReportBase.custom_round(membership.prima_insurance/100 * membership.insurable_remuneration, 2)
                else:
                    afp_si = ReportBase.custom_round(membership.prima_insurance/100 * record.total_vacation, 2)
                if record.contract_id.commision_type == 'mixed':
                    afp_mixed_com = ReportBase.custom_round(membership.mixed_commision/100 * record.total_vacation, 2)
                    afp_fixed_com =0
                elif record.contract_id.commision_type == 'flow':
                    afp_fixed_com = ReportBase.custom_round(membership.fixed_commision /100 * record.total_vacation, 2)
                    afp_mixed_com =0
            else:
                onp = ReportBase.custom_round(membership.retirement_fund/100 * record.total_vacation, 2)
            record.afp_jub = afp_jub
            record.afp_si = afp_si
            record.afp_mixed_com = afp_mixed_com
            record.afp_fixed_com = afp_fixed_com
            record.onp = onp
            record.total = ReportBase.custom_round(record.total_vacation - afp_jub - afp_si - afp_mixed_com - afp_fixed_com - onp, 2)
            if not record.total > 0 and not self._context.get('line_form', False):
                record.unlink()

# class HrCompensationLine(models.Model):
#     _name = 'hr.compensation.line'
#     _description = 'Compensation Line'
#
#     liquidation_id = fields.Many2one('hr.liquidation', ondelete='cascade')
#     employee_id = fields.Many2one('hr.employee')
#     contract_id = fields.Many2one('hr.contract')
#     identification_id = fields.Char(related='employee_id.identification_id', string='Nro Documento')
#     last_name = fields.Char(related='employee_id.last_name', string='Apellido Paterno')
#     m_last_name = fields.Char(related='employee_id.m_last_name', string='Apellido Materno')
#     names = fields.Char(related='employee_id.names', string='Nombres')
#     admission_date = fields.Date(string='Fecha de Ingreso')
#     cessation_date = fields.Date(string='Fecha de Cese')
#     total = fields.Float(string='Total')
#
#     preserve_record = fields.Boolean('No Recalcular')

class HrLiquidationExtraConcepts(models.Model):
    _name = 'hr.liquidation.extra_concepts'
    _description = 'Hr Liquidation Extra Concepts'

    liquidation_id = fields.Many2one('hr.liquidation', ondelete='cascade')
    employee_id = fields.Many2one('hr.employee', string='Empleado')
    contract_id = fields.Many2one('hr.contract', string='Contrato')
    identification_id = fields.Char(related='employee_id.identification_id', string='Nro Documento')
    admission_date = fields.Date(string='Fecha de Ingreso')
    cessation_date = fields.Date(string='Fecha de Cese')
    concept_ids = fields.One2many('hr.extra.concept', 'concept_id', string='Conceptos Extras')
    income = fields.Float(string='Ingresos')
    expenses = fields.Float(string='Descuentos')

    preserve_record = fields.Boolean('No Recalcular')

    def get_concepts_view(self):
        return self.env['hr.extra.concept'].get_wizard(self.employee_id.id,self.liquidation_id.id,self.id)

class HrExtraConcept(models.Model):
    _name = 'hr.extra.concept'
    _description = 'Hr Extra Concept'

    conceptos_lines = fields.One2many('hr.extra.concept.line','extra_concept_id')
    liquidation_id = fields.Many2one('hr.liquidation', ondelete='cascade')
    employee_id = fields.Many2one('hr.employee', string='Empleado')
    concept_id = fields.Many2one('hr.liquidation.extra_concepts', ondelete='cascade')

    def get_wizard(self,employee_id,liquidation_id,concept_id):
        res_id = self.env['hr.extra.concept'].search([('concept_id','=',concept_id)],limit=1)
        res_id = res_id.id if res_id else self.id
        return {
            'name':'Conceptos Adicionales',
            'type':'ir.actions.act_window',
            'res_id':res_id,
            'view_type':'form',
            'view_mode':'form',
            'res_model':'hr.extra.concept',
            'views':[[self.env.ref('hr_social_benefits.hr_extra_concept_form').id,'form']],
            'target':'new',
            'context':{
                'default_employee_id':employee_id,
                'default_liquidation_id':liquidation_id,
                'default_concept_id':concept_id
            }
        }
    # @api.depends('concept_ids')
    # def get_income_discount(self):
    #     for rec in self:
    #         In_Concepts = rec.concept_ids.filtered(lambda l: l.type == 'in')
    #         Out_Concepts = rec.concept_ids.filtered(lambda l: l.type == 'out')
    #         rec.income = sum(In_Concepts.mapped('amount')) if In_Concepts else 0
    #         rec.expenses = sum(Out_Concepts.mapped('amount')) if Out_Concepts else 0

    def add_concept(self):
        In_Concepts = Out_Concepts = 0
        if self.conceptos_lines:
            for line in self.conceptos_lines:
                if line.type == 'in':
                    In_Concepts += line.amount
                elif line.type == 'out':
                    Out_Concepts += line.amount
            self.env['hr.liquidation.extra_concepts'].browse(self.concept_id.id).write({'income':In_Concepts,'expenses':Out_Concepts})
        else:
            self.env['hr.liquidation.extra_concepts'].browse(self.concept_id.id).write({'income':0,'expenses':0})
        return self.env['hr.liquidation'].browse(self.liquidation_id.id).liq_ext_concept_ids.refresh()

class HrExtraConceptLine(models.Model):
    _name = 'hr.extra.concept.line'
    _description = 'Hr Extra Concept Line'

    extra_concept_id = fields.Many2one('hr.extra.concept', ondelete='cascade')
    name_input_id = fields.Many2one('hr.payslip.input.type', string='Descripcion')
    amount = fields.Float(string='Monto')
    type = fields.Selection([('in', 'Ingreso'),('out', 'Descuento')], string='Tipo', default='in')