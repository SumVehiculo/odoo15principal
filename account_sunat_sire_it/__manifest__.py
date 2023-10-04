# -*- encoding: utf-8 -*-
{
	'name': 'ACCOUNT SUNAT SIRE',
	'category': 'account',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['account_sunat_it','popup_it','account_report_menu_it'],
	'version': '1.0',
	'description':"""
	- ACCOUNT SUNAT SIRE
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
        'SQL.sql',
        'security/security.xml',
        'security/ir.model.access.csv',
		'views/account_main_parameter.xml',
		'views/account_sunat_sire_sale_data.xml',
		'wizards/account_sunat_rep.xml'
	],
	'installable': True
}