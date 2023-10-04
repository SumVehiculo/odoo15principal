# -*- encoding: utf-8 -*-
{
	'name': 'Verificacion SUNAT',
	'category': 'account',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['account_fields_it'],
	'version': '1.0',
	'description':"""
	- Verificacion SUNAT
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/security.xml',
		'security/ir.model.access.csv',
		'views/account_move.xml',
		'views/account_main_parameter.xml',
        'views/account_query_sunat.xml'
		],
	'installable': True
}
