# -*- encoding: utf-8 -*-
{
	'name': 'Reporte Balances e Inventarios V2',
	'category': 'account',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['account_sunat_it','account_base_sunat_balance_inventory_v2','account_financial_situation_it','account_efective_it','account_patrimony_it','account_rfun_rep_it'],
	'version': '1.0',
	'description':"""
		- PLEs Balances e Inventarios 
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'wizards/account_sunat_rep.xml'
	],
	'installable': True
}