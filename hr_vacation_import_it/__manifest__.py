# -*- coding: utf-8 -*-
{
    'name': 'Import Vacations Rest',
    'category': 'hr',
    'author': 'ITGRUPO-HR',
    'depends': ['hr_vacations_it'],
    'version': '1.0',
    'description': """
        Modulo para importar saldos de descansos vacacionales
     """,
    'auto_install': False,
    'data': [
        'security/ir.model.access.csv',
        'data/attachment_sample.xml',
        'views/hr_vacation_rest_import_view.xml',
    ],
    'installable': True,
    'license': 'LGPL-3',
}
