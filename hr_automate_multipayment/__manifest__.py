# -*- coding: utf-8 -*-
{
    'name': "Hr Automate Multipayment",
    'category': 'hr',
	'author': 'ITGRUPO-HR',
    'depends': ['hr_fields_it', 'hr_social_benefits','hr_importers_it','report_tools'],
    'version': '1.0',
    'description': """
        Este módulo gestiona los pagos multiples de los empleados con las entidades bancarias.
    """,
    'auto_install': False,
	'demo': [],
    'data': [
        'security/security.xml',
		'security/ir.model.access.csv',
        'data/hr_type_document.xml',
        'views/res_bank.xml',
        'views/res_partner_bank.xml',
        'views/hr_automate_multipayment.xml',
        'views/hr_main_parameter.xml',
        'views/hr_payslip_run.xml',
        'views/hr_cts.xml',
        'views/hr_gratification.xml',
    ],
    'installable': True,
	'license': 'LGPL-3',
}
