# -*- encoding: utf-8 -*-
{
	'name': 'Reporte BASE - PLE Balances e Inventarios',
	'category': 'account',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['account_base_sunat_it'],
	'version': '1.0',
	'description':"""
		- PLEs Balances e Inventarios
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/security.xml',
		'security/ir.model.access.csv',
		'views/menu_items.xml',
		'views/sunat_table_data.xml',
		'views/account_register_values_it.xml'
	],
	'installable': True
}