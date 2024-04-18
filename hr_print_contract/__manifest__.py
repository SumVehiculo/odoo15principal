# -*- coding: utf-8 -*-
{
    'name' : 'Hr Contratos personalizados',
    'category': 'hr',
    "author": "ITGRUPO-HR",
    'depends': ['hr_fields_it'],
    'version': '1.0',
    'description':"""Módulo para la impresión de contratos de empleados y operarios""",
    'auto_install': False,
    'data': [
        # 'data/type_contract_data.xml',
        'views/hr_contract.xml',
        'views/hr_contract_history.xml',
        'report/contract_employee.xml',
    ],
    'installable': True,
	'license': 'LGPL-3',
}
