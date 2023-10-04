# -*- encoding: utf-8 -*-
{
	'name': 'Ausencias IT',
	'category': 'hr',
	'author': 'ITGRUPO-HR',
	'depends': ['hr_fields_it','hr_vacations_it','hr_social_benefits'],
	'version': '1.0',
	'description':"""
	Registro de asuencias/vacaciones
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/security.xml',
		'security/ir.model.access.csv',
		'data/hr_leave_type_data.xml',
		'views/hr_parameter_view.xml',
		'views/hr_leave_type.xml',
		'views/hr_leave.xml',
		'views/hr_vacation.xml',
		'views/hr_menus.xml',
	],
	'installable': True,
	'assets': {
		'web.assets_backend': [
			'hr_leave_it/static/src/js/radio_image.js',
		],
		'web.assets_qweb': [
			'hr_leave_it/static/src/xml/*.xml',
		],
	},
	'license': 'LGPL-3',
}