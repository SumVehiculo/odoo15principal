# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from datetime import date

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    def open_wizard_certificate(self):
        return {
            'name': 'Certificado de Trabajo PDF',
            'res_model': 'hr.certificate.wizard',
            'view_mode': 'form',
            'view_type': 'form',
            'context': {'default_employee_id': self.id},
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    def open_wizard_letter(self):
        return {
            'name': 'Carta Retiro PDF',
            'res_model': 'hr.letter.wizard',
            'view_mode': 'form',
            'view_type': 'form',
            'context': {'default_employee_id': self.id},
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

class certificate(models.TransientModel):
    _name = 'hr.certificate.wizard'
    _description = 'certificate'

    employee_id = fields.Many2one('hr.employee', string='Empleado a Certificar')
    des_empl = fields.Selection([
        ('el Sr.', 'Señor'),
        ('la Sra.', 'Señora'),
        ('la Srta.', 'Señorita')
    ], string='Tratamiento',default="el Sr.")
    # employee_firma = fields.Many2one('hr.employee', string='Empleado que Firma')
    date_ini = fields.Date(string='Fecha Inicial')
    date_fin = fields.Date(string='Fecha Final')
    city = fields.Char(string='Ciudad')

    company_id = fields.Many2one('res.company', string=u'Compañia', default=lambda self: self.env.company.id)
    main_parameter_id = fields.Many2one('hr.main.parameter', string='parametro')

    day = fields.Integer(string='Dia')
    month = fields.Char(string='Mes')
    year = fields.Integer(string='Año')

    @api.model
    def default_get(self, fields):
        res = super(certificate, self).default_get(fields)
        MainParameter = self.env['hr.main.parameter'].get_main_parameter()
        employee_id = res.get('employee_id')
        employee = self.env['hr.employee'].search([('id', '=',employee_id)], limit=1)
        situation_id = self.env['hr.situation'].search([('code', '=', '0')], limit=1)
        # print("employee",employee)
        last_contract = self.env['hr.contract'].search([('employee_id', '=', employee_id),
                                                        ('situation_id', '=', situation_id.id)], limit=1)
        first_contract = self.env['hr.contract'].get_first_contract(employee, last_contract)
        # print("first_contract",first_contract)

        date_fin = last_contract.date_end
        date_ini = first_contract.date_start
        res.update({'main_parameter_id': MainParameter.id,
                    'date_fin': date_fin,
                    'date_ini': date_ini,
                    'city': self.env.company.city,
                    'des_empl': 'el Sr.' if employee.gender == 'male' else 'la Srta.' })
        return res

    def export_certificate(self):
        # current_date = date.today()
        current_date = self.date_fin
        ar = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Setiembre', 'Octubre', 'Noviembre', 'Diciembre']
        self.day = current_date.day
        self.month = ar[current_date.month - 1]
        self.year = current_date.year

        if self.employee_id.id == False:
            raise ValidationError('Ingrese Empleado')
        if self.des_empl == False:
            raise ValidationError('Ingrese Descripción de Empleado a Certificar')
        # if self.employee_firma.id == False:
        #     raise ValidationError('Ingrese Empleado que Firmará')
        if self.city == False:
            raise ValidationError('Ingrese Ciudad')
        if self.date_ini == False:
            raise ValidationError('Ingrese Fecha Inicial')
        if self.date_fin == False:
            raise ValidationError('Ingrese Fecha Final')
        return self.env.ref('hr_certificate_letter_it.action_report_certificate').report_action(self)


class letter(models.TransientModel):
    _name = 'hr.letter.wizard'
    _description = 'letter'

    employee_id = fields.Many2one('hr.employee', string='Empleado')
    des_empl = fields.Selection([
        ('el Sr.', 'Señor'),
        ('la Sra.', 'Señora'),
        ('la Srta.', 'Señorita')
    ], string='Tratamiento',default="el Sr.")
    # employee_firma = fields.Many2one('hr.employee', string='Empleado que Firma')
    # bank = fields.Many2one('res.bank', string='Banco')
    date_fin = fields.Date(string='Fecha de Cese')
    city = fields.Char(string='Ciudad')

    company_id = fields.Many2one('res.company', string=u'Compañia', default=lambda self: self.env.company.id)
    main_parameter_id = fields.Many2one('hr.main.parameter', string='parametro')

    day_fin = fields.Integer(string='Dia')
    month_fin = fields.Char(string='Mes')
    year_fin = fields.Integer(string='Año')

    @api.model
    def default_get(self, fields):
        res = super(letter, self).default_get(fields)
        MainParameter = self.env['hr.main.parameter'].get_main_parameter()
        employee_id = res.get('employee_id')
        employee = self.env['hr.employee'].search([('id', '=',employee_id)], limit=1)
        situation_id = self.env['hr.situation'].search([('code', '=', '0')], limit=1)
        # print("employee_id",employee_id)
        last_contract = self.env['hr.contract'].search([('employee_id', '=', employee_id),
                                                        ('situation_id', '=', situation_id.id)], limit=1)
        # print("last_contract",last_contract)
        date_fin = last_contract.date_end
        res.update({'main_parameter_id': MainParameter.id,
                    'date_fin': date_fin,
                    'city': self.env.company.city,
                    'des_empl': 'el Sr.' if employee.gender == 'male' else 'la Srta.' })
        return res

    def export_letter(self):
        # current_date = date.today()
        ar = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Setiembre', 'Octubre', 'Noviembre', 'Diciembre']
        # self.day_now = current_date.day
        # self.month_now = ar[current_date.month - 1]
        # self.year_now = current_date.year

        self.day_fin = self.date_fin.day
        self.month_fin = ar[self.date_fin.month - 1]
        self.year_fin = self.date_fin.year

        if self.employee_id.id == False:
            raise ValidationError('Ingrese Empleado')
        if self.des_empl == False:
            raise ValidationError('Ingrese Descripción de Empleado a Certificar')
        # if self.employee_id.id == False:
        #     raise ValidationError('Ingrese Empleado Firma')
        # if self.bank.id == False:
        #     raise ValidationError('Ingrese Banco')
        if self.city == False:
            raise ValidationError('Ingrese Ciudad')
        if self.date_fin == False:
            raise ValidationError('Ingrese Fecha Final')
        return self.env.ref('hr_certificate_letter_it.action_report_letter').report_action(self)
