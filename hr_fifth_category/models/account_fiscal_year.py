# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from datetime import *

class AccountFiscalYear(models.Model):
    _inherit = 'account.fiscal.year'

    uit = fields.Float(string='Valor de UIT')

class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    # name = fields.Many2one(default=lambda self:self.get_period().id)

    def get_period(self):
        fiscal_year = self.env['hr.main.parameter'].search([('company_id','=',self.env.company.id)],limit=1).fiscal_year_id
        if not fiscal_year:
            raise UserError(u'No se ha configurado un Año Fiscal en parametros principales de Nominas')
        else:
            today = date.today()
            period = self.env['hr.period'].search([('fiscal_year_id', '=', fiscal_year.id),
                                                   ('date_start', '<=', today),
                                                   ('date_end', '>=', today)],limit=1)
            # print("period",period)
            if not period:
                raise UserError('No se encontro Periodo para la Fecha Actual')
            else:
                return period