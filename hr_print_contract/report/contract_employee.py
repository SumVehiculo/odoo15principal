# -*- coding: utf-8 -*-

import time
from odoo import models, fields, api, _
from datetime import date
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError
import calendar

from jinja2 import Template
import subprocess
import sys

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

try:
    import arrow
except:
    install('arrow')


class report_contract_employee(models.AbstractModel):
    _name = 'report.hr_print_contract.report_contract_employee'
    _description = 'Contract Employee Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['hr.contract'].browse(docids)
        for doc in docs:
            if not doc.contract_type_id:
                raise UserError('No se puede generar un reporte si no se ha definido una Plantilla para el contrato')
        return {
            'doc_ids': docs.ids,
            'doc_model': 'hr.contract',
            'data': data,
            'docs': docs,
            'conversion': self._conversion,
        }

    def _fecha_str(self, city):
        date = time.strftime("%Y-%m-%d")
        day = time.strftime('%d', time.strptime(date,'%Y-%m-%d'))
        month = time.strftime('%B', time.strptime(date,'%Y-%m-%d')).upper()
        year = time.strftime('%Y', time.strptime(date,'%Y-%m-%d'))
        fecha = str(city).upper() + " , " + " " + day + " de " + month + " del " + year
        return fecha

    def get_num_month(self, start,end):
        num_month = 0
        for d in arrow.Arrow.range('month',start,end):
            num_month +=1
        return num_month

    def _conversion(self, template, code):
        # template = 'Hey, my name is {{ custom_function(first_name) }}'
        jinga_html_template = Template(template)
        # jinga_html_template.globals['custom_function'] = custom_function

        row = self.env['hr.contract'].browse(code)

        MainParameter = self.env['hr.main.parameter'].get_main_parameter()

        current_date = date.today()
        date_now = '{0} de {1} del {2}'.format(
            current_date.day,
            MainParameter.get_month_name(current_date.month),
            current_date.year,
        )

        if row.date_start:
            date_start = '{0} de {1} del {2}'.format(
                row.date_start.day,
                MainParameter.get_month_name(row.date_start.month),
                row.date_start.year,
            )
        else:
            date_start = ''

        if row.date_end:
            date_end = '{0} de {1} del {2}'.format(
                row.date_end.day,
                MainParameter.get_month_name(row.date_end.month),
                row.date_end.year,
            )
        else:
            date_end = ''

        if row.date_start and row.date_end:
            months = (row.date_end.year - row.date_start.year) * 12 + row.date_end.month - row.date_start.month
            days = row.date_end.day - row.date_start.day + 1
            if days < 0:
                days = 0
            months = '%s mes(es) y %s dia(as)' % (str(months), str(days))
        else:
            months = 'indefinido'

        if row.date_start and row.trial_date_end:
            months_prueba = (
                                        row.trial_date_end.year - row.date_start.year) * 12 + row.trial_date_end.month - row.date_start.month
            days_prueba = row.trial_date_end.day - row.date_start.day + 1
            if days_prueba < 0:
                days_prueba = 0
            months_prueba = '%s mes(es) y %s dia(as)' % (str(months_prueba), str(days_prueba))
        else:
            months_prueba = 'indefinido'

        letter_Wage = MainParameter.number_to_letter(row.wage)
        fields = {
            'nombre_empleador': row.company_id.name if row.company_id.name else "",
            'ruc_empleador': row.company_id.vat if row.company_id.vat else "",
            'direccion_empleador': row.company_id.street_name if row.company_id.street_name else "",
            'distrito': row.company_id.partner_id.district_id.name if row.company_id.partner_id.district_id.name else "",
            'provincia': row.company_id.partner_id.province_id.name if row.company_id.partner_id.province_id.name else "",
            'departamento': row.company_id.partner_id.state_id.name if row.company_id.partner_id.state_id.name else "",
            'cargo_RL': MainParameter.employee_in_charge_id.job_id.name if MainParameter.employee_in_charge_id.job_id.name else "",
            'apoderado': MainParameter.employee_in_charge_id.name if MainParameter.employee_in_charge_id.name else "",
            'dni_apoderado': MainParameter.employee_in_charge_id.identification_id if MainParameter.employee_in_charge_id.identification_id else "",
            'nombre_trabajador': row.employee_id.name if row.employee_id.name else "",
            'estado_civil_trabajador': dict(row.employee_id._fields['marital'].selection) if row.employee_id.marital else "",
            'sexo_trabajador': dict(row.employee_id._fields['gender'].selection) if row.employee_id.gender else "",
            'td_trabajador': row.employee_id.type_document_id.name if row.employee_id.type_document_id.name else "",
            'dni_trabajador': row.employee_id.identification_id if row.employee_id.identification_id else "",
            'nacionalidad_trabajador': row.employee_id.country_id.name if row.employee_id.country_id.name else "",
            'direccion_trabajador': row.employee_id.address if row.employee_id.address else "",
            'titulo_trabajo': row.job_id.name if row.job_id.name else "",
            'area': row.department_id.name if row.department_id.name else "",
            'salario': str('{0:.2f}'.format(row.wage)),
            'salario_letras': letter_Wage,
            'moneda': "SOLES",
            'meses': months,
            'fecha_inicio': date_start,
            'fecha_fin': date_end,
            'fecha_prueba_fin': months_prueba,
            'funciones_empleado': row.job_id.description if row.job_id.description else "",
            'horas_jornada': row.resource_calendar_id.hours_per_day if row.resource_calendar_id.hours_per_day else "",
            'lugar_contrato': row.company_id.partner_id.state_id.name if row.company_id.partner_id.state_id.name else "",
            'fecha_firma': date_now,
            # 'plazo_meses': self.get_num_month(datetime.strptime(row.date_start, '%Y-%m-%d'), datetime.strptime(row.date_end, '%Y-%m-%d')),
        }
        # print("fields",fields)

        return jinga_html_template.render(**fields)
