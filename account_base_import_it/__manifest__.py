# -*- encoding: utf-8 -*-
{
	'name': 'Menu Importadores',
	'category': 'import',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['account_fields_it','contacts'],
	'version': '1.0',
	'description':"""
		- Menu Importadores
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/security.xml',
		'views/account_import_menu.xml'
	],
	'installable': True,
	'license': 'LGPL-3'
}