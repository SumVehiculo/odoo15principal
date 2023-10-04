# -*- encoding: utf-8 -*-
{
	'name': 'Tesoreria IT',
	'category': 'account',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['account_fields_it','account_batch_payment'],
	'version': '1.0',
	'description':"""
	- Tesoreria IT
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/security.xml',
		'security/ir.model.access.csv',
		'views/account_batch_payment.xml',
		'views/account_payment.xml',
		'views/account_bank_statement.xml',
		'views/account_treasury_menu.xml'
		],
	'installable': True,
	'license': 'LGPL-3'
}
