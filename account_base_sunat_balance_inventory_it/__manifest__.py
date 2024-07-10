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
		'SQL.sql',
		'views/account_type_it.xml',
		'views/account_main_parameter.xml',
		'views/menu_items.xml',
        'views/account_sunat_checking_balance.xml',
        'views/account_sunat_shareholding.xml',
        'views/account_sunat_capital.xml',
        'views/account_sunat_state_patrimony.xml',
        'views/account_sunat_integrated_results.xml',
        'views/account_sunat_efective_flow.xml',
		'views/account_register_values_it.xml'
	],
	'installable': True
}