# -*- encoding: utf-8 -*-
{
	'name': 'Modificaciones en Reportes de Caja y Bancos',
	'category': 'account',
	'author': 'ITGRUPO',
	'depends': ['account_fields_it','account_bank_rep_it','account_cash_rep_it','account_sunat_it'],
	'version': '1.0',
	'description':"""
	- Campos y funcionalidad para Flujo de Caja
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'views/account_main_parameter.xml',
	],
	'installable': True
}