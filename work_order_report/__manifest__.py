# -*- encoding: utf-8 -*-
{
    'name': 'Reporte General Orden de Trabajo',
    'version': '1.0',
    'description': 'Crea el Wizard del "Reporte General OT"',
    'author': 'ITGRUPO, Jhorel Revilla',
    'license': 'LGPL-3',
    'depends': [
        'work_order'
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizards/work_order_report_wizard.xml',
        
    ],
    'auto_install': False,
    'application': False
}