# -*- encoding: utf-8 -*-
{
	'name': 'Hr Voucher IT Inherit',
	'category': 'hr',
	'author': 'ITGRUPO-HR',
	'depends': ['hr_voucher_it'],
	'version': '1.0',
	'description':"""
	Modulo para Boletas de pago en Nominas - SUM VEHICULOS
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/security.xml',
		'security/ir.model.access.csv',
		'data/hr_situation_special.xml',
		'views/hr_employee.xml',
		'views/hr_situation_special.xml',
		'views/hr_contract.xml',
	],
	'installable': True,
	'license': 'LGPL-3',
}
