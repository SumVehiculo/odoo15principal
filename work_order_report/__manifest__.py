# -*- encoding: utf-8 -*-
{
    'name': 'Reporte General Orden de Trabajo',
    'version': '1.0',
    'description': 'Crea el Wizard del "Reporte General OT"',
    'author': 'ITGRUPO, Jhorel Revilla',
    'license': 'LGPL-3',
    'depends': [
        'work_order',
        'employees_hourly_cost'
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizards/work_order_report_wizard.xml',
        'views/account_analytic_line.xml',
        'views/general_work_order_report.xml',
        'views/general_work_order_report_total.xml'
    ],
    'auto_install': False,
    'application': False
}