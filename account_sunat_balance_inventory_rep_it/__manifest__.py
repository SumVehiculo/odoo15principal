# -*- encoding: utf-8 -*-
{
	'name': 'Reporte PLE Balances e Inventarios',
	'category': 'account',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['account_base_sunat_balance_inventory_it','om_account_asset','kardex_valorizado_cuentas_contables_it','kardex_fields_it','stock_account_it'],
	'version': '1.0',
	'description':"""
		- PLEs Balances e Inventarios
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/ir.model.access.csv',
		'SQL.sql',
		'wizards/popup_it_balance_inventory.xml',
		'wizards/account_sunat_balance_inventory_rep.xml'
	],
	'installable': True
}