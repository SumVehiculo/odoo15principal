# -*- encoding: utf-8 -*-
{
	'name': 'Hr Vacations it',
	'category': 'hr',
	'author': 'ITGRUPO-HR',
	'depends': ['hr_fields_it'],
	'version': '1.0',
	'description':"""
		Modulo de Vacaciones en Planilla por ITGrupo
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/security.xml',
		'security/ir.model.access.csv',
		'wizard/hr_vacation_rest_wizard.xml',
		'views/hr_payslip.xml',
		'views/hr_vacation_rest.xml',
		'views/hr_menus.xml'
	],
	'installable': True,
	'license': 'LGPL-3',
}