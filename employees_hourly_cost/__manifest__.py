# -*- encoding: utf-8 -*-
{
    'name': 'Empleados Costo por Hora',
    'version': '1.0',
    'description': 'Crea la tabla costo por hora para calcularse en la parte de horas',
    'author': 'ITGRUPO, Jhorel Revilla',
    'license': 'LGPL-3',
    'depends': [
        'analytic',
        'hr_timesheet',
        'mail'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_employee_hourly_cost.xml',
    ],
    'auto_install': False,
    'application': False
}