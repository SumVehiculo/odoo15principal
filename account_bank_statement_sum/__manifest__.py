# -*- encoding: utf-8 -*-
{
	'name': 'Aprobacion Caja Chica',
	'category': 'account',
	'author': 'ITGRUPO, Moises L',
	'depends': ['account_fields_it','account_treasury_it'],
	'version': '1.0',
	'description':"""
		Agrega la aprobacion de la caja chica
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
        'security/security.xml',
		'views/account_bank_statement.xml',
	],
	'installable': True,
	'license': 'LGPL-3'
}
