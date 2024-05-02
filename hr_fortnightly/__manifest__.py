# -*- encoding: utf-8 -*-
{
	'name': 'Hr Pagos Quincenales',
	'category': 'hr',
	'author': 'ITGRUPO-HR',
	'depends': ['hr_advances_and_loans'],
	'version': '1.0',
	'description':"""
	Gestion de pagos quincenales
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/ir.model.access.csv',
		'security/security.xml',
		'data/hr_advance_type_data.xml',
		'data/hr_loan_type_data.xml',
		'views/hr_quincena_views.xml',
		'views/hr_main_parameter.xml'
			],
	'installable': True,
	'license': 'LGPL-3',
}