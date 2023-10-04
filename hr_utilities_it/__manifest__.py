# -*- encoding: utf-8 -*-
{
	'name': 'Hr Utilities',
	'category': 'hr',
	'author': 'ITGRUPO-HR',
	'depends': ['hr_fields_it'],
	'version': '1.0',
	'description':"""
	- Modulo para Utilidades
	""",
	'auto_install': False,
	'demo': [],
	'data':	['security/security.xml',
			 'security/ir.model.access.csv',
			 'wizard/hr_utilities_print_wizard.xml',
			 'views/hr_utilities_it.xml',
			 'views/hr_main_parameter.xml'
			],
	'installable': True,
	'license': 'LGPL-3',
}
