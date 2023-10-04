# -*- encoding: utf-8 -*-
{
	'name': 'Hr Provisions',
	'category': 'hr',
	'author': 'ITGRUPO-HR',
	'depends': ['hr_social_benefits'],
	'version': '1.0',
	'description':"""
	Modulo de Provisiones	
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/security.xml',
		'security/ir.model.access.csv',
		'views/hr_main_parameter.xml',
		'views/hr_provisions.xml',
		'wizard/hr_provisions_wizard.xml'
	],
	'installable': True,
	'license': 'LGPL-3',
}
