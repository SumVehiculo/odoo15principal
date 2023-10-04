# -*- encoding: utf-8 -*-
{
	'name': 'Hr Social Benefits',
	'category': 'hr',
	'author': 'ITGRUPO-HR',
	'depends': ['hr_fields_it', 'account', 'report_tools', 'popup_it'],
	'version': '1.0',
	'description':"""
	Modulo para Beneficios Sociales
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/security.xml',
		'security/ir.model.access.csv',
		'views/hr_employee.xml',
		'views/hr_gratification.xml',
		'views/hr_cts.xml',
		'views/hr_liquidation.xml',
		'views/hr_menus.xml',
		'views/hr_main_parameter.xml'
	],
	'installable': True,
	'license': 'LGPL-3',
}
