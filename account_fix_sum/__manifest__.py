# -*- encoding: utf-8 -*-
{
	'name': 'Correcciones Contabilidad SUM',
	'category': 'account',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua, Sebastian Moises Loraico Lopez',
	'depends': ['account_fields_it'],
	'version': '1.0',
	'description':"""
	- Correcciones Contabilidad para SUM
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
        'views/account_bank_statement.xml',
        'views/account_move.xml'
	],
	'installable': True,
	'license': 'LGPL-3'
}
