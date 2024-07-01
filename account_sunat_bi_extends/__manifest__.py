# -*- encoding: utf-8 -*-
{
	'name': 'Reporte PLE BI Resultados Integrales',
	'category': 'account',
	'author': 'ITGRUPO',
	'depends': ['account_sunat_balance_inventory_rep_it'],
	'version': '1.0',
	'description':"""
		- PLEs Balances e Inventarios con nueva tabla de resultados integrales
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/ir.model.access.csv',
		'views/account_account.xml',
		'views/account_integrated_results_catalog_views.xml'
	],
	'installable': True
}