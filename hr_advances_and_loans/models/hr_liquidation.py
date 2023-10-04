# -*- coding:utf-8 -*-
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError
from datetime import *
from calendar import *
from dateutil.relativedelta import relativedelta
import base64

class HrLiquidation(models.Model):
    _inherit = 'hr.liquidation'

    def import_advances(self):
        MainParameter = self.env['hr.main.parameter'].get_main_parameter()
        if not MainParameter.cts_advance_id:
            raise UserError(
                'No se ha configurado un tipo de adelanto para Liquidacion en Parametros Generales de la pestaña Liquidacion')
        log = ''
        Lot = self.payslip_run_id
        to_create = []
        for line in self.liq_ext_concept_ids:
            sql = """
    			select sum(ha.amount) as amount,
    			ha.employee_id,
    			hat.input_id
    			from hr_advance ha
    			inner join hr_advance_type hat on hat.id = ha.advance_type_id
    			where ha.discount_date >= '{0}' and
    				  ha.discount_date <= '{1}' and
    				  ha.employee_id = {2} and
    				  ha.state = 'not payed' and
    				  hat.id = {3}
    			group by ha.employee_id, hat.input_id
    			""".format(Lot.date_start, Lot.date_end, line.employee_id.id, MainParameter.liqui_advance_id.id)
            self._cr.execute(sql)
            res_data = self._cr.dictfetchall()
            # print("res_data",res_data)

            if res_data:
                hec = self.env['hr.extra.concept'].search([('concept_id', '=', line.id)], limit=1)
                if len(hec):
                    vals = {
                        'extra_concept_id':hec.id,
                        'name_input_id': res_data[0]['input_id'],
                        'amount': res_data[0]['amount'],
                        'type': 'out',
                    }
                    to_create.append(vals)
                    # print("vals if",vals)

                    for v in to_create:
                        hecl = self.env['hr.extra.concept.line'].search([('extra_concept_id', '=', v['extra_concept_id']),('name_input_id', '=', v['name_input_id'])])
                        if len(hecl):
                            hecl[0].write(v)
                            hec.add_concept()
                            log += '%s\n' % line.employee_id.name
                            # print("if hecl",hecl.name_input_id.name)
                        else:
                            self.env['hr.extra.concept.line'].create(v)
                            hec.add_concept()
                            log += '%s\n' % line.employee_id.name
                            # print("else hecl",hec.employee_id.name)
                else:
                    data = {
                        'concept_id': line.id,
                        'employee_id': line.employee_id.id,
                        'liquidation_id': line.liquidation_id.id,
                        'conceptos_lines': [(0, 0, {
                            'name_input_id': advance['input_id'],
                            'amount': advance['amount'],
                            'type': 'out',
                        }) for advance in res_data
                    ]}
                    # print('val',vals)
                    compute_total = self.env['hr.extra.concept'].create(data)
                    compute_total.add_concept()
                    log += '%s\n' % line.employee_id.name

            self.env['hr.advance'].search([('discount_date', '>=', Lot.date_start),
										   ('discount_date', '<=', Lot.date_end),
										   ('employee_id', '=', line.employee_id.id),
										   ('state', '=', 'not payed'),
										   ('advance_type_id.id', '=', MainParameter.liqui_advance_id.id)]).turn_paid_out()
        if log:
            return self.env['popup.it'].get_message('Se importo adelantos a los siguientes empleados:\n' + log)
        else:
            return self.env['popup.it'].get_message('No se importo ningun adelanto')

    def import_loans(self):
        MainParameter = self.env['hr.main.parameter'].get_main_parameter()
        if not MainParameter.cts_advance_id:
            raise UserError(
                'No se ha configurado un tipo de prestamo para Liquidacion en Parametros Generales de la pestaña Liquidacion')
        log = ''
        Lot = self.payslip_run_id
        to_create = []
        for line in self.liq_ext_concept_ids:
            sql = """
    			select sum(hll.amount) as amount,
				hll.employee_id,
    			hlt.input_id
    			from hr_loan_line hll
				inner join hr_loan_type hlt on hlt.id = hll.loan_type_id
    			where hll.date >= '{0}' and
					  hll.date <= '{1}' and
					  hll.employee_id = {2} and
					  hll.validation = 'not payed' and
					  hlt.id = {3}
    			group by hll.employee_id, hlt.input_id
    			""".format(Lot.date_start, Lot.date_end, line.employee_id.id, MainParameter.liqui_loan_id.id)
            self._cr.execute(sql)
            res_data = self._cr.dictfetchall()

            if res_data:
                hec = self.env['hr.extra.concept'].search([('concept_id', '=', line.id)], limit=1)
                if len(hec):
                    vals = {
                        'extra_concept_id': hec.id,
                        'name_input_id': res_data[0]['input_id'],
                        'amount': res_data[0]['amount'],
                        'type': 'out',
                    }
                    to_create.append(vals)
                    # print("vals if",vals)

                    for v in to_create:
                        hecl = self.env['hr.extra.concept.line'].search(
                            [('extra_concept_id', '=', v['extra_concept_id']), ('name_input_id', '=', v['name_input_id'])])
                        if len(hecl):
                            hecl[0].write(v)
                            hec.add_concept()
                            log += '%s\n' % line.employee_id.name
                            # print("if hecl",hecl.name_input_id.name)
                        else:
                            self.env['hr.extra.concept.line'].create(v)
                            hec.add_concept()
                            log += '%s\n' % line.employee_id.name
                            # print("else hecl",hec.employee_id.name)
                else:
                    data = {
                        'concept_id': line.id,
                        'employee_id': line.employee_id.id,
                        'liquidation_id': line.liquidation_id.id,
                        'conceptos_lines': [(0, 0, {
                            'name_input_id': loan['input_id'],
                            'amount': loan['amount'],
                            'type': 'out',
                        }) for loan in res_data
                    ]}
                    # print('val',vals)
                    compute_total = self.env['hr.extra.concept'].create(data)
                    compute_total.add_concept()
                    log += '%s\n' % line.employee_id.name

            self.env['hr.loan.line'].search([('date', '>=', Lot.date_start),
                                             ('date', '<=', Lot.date_end),
                                             ('employee_id', '=', line.employee_id.id),
                                             ('validation', '=', 'not payed'),
                                             ('loan_type_id.id', '=', MainParameter.liqui_loan_id.id)]).turn_paid_out()

        if log:
            return self.env['popup.it'].get_message('Se importo prestamos a los siguientes empleados:\n' + log)
        else:
            return self.env['popup.it'].get_message('No se importo ningun prestamo')

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

        # inp_adv = MainParameter.liqui_advance_id.input_id
        # inp_loan = MainParameter.liqui_loan_id.input_id
        for line in self.liq_ext_concept_ids:
            Slip = Lot.slip_ids.filtered(lambda slip: slip.employee_id == line.employee_id)
            for line_input in line.concept_ids:
                # total_des=0
                for line in line_input.conceptos_lines:
                    # if line.name_input_id == inp_adv or line.name_input_id == inp_loan:
                    #     extra_line = Slip.input_line_ids.filtered(lambda inp: inp.input_type_id.code == 'DES_BBSS')
                    #     total_des += line.amount
                    #     extra_line.amount = total_des
                    # else:
                    extra_line = Slip.input_line_ids.filtered(lambda inp: inp.input_type_id == line.name_input_id)
                    extra_line.amount = line.amount
                    # print("codigo",extra_line.code)

        self.state = 'exported'
        return self.env['popup.it'].get_message('Se exporto exitosamente')