# -*- encoding: utf-8 -*-
{
	'name': 'Reporte Flujo de Caja',
	'category': 'account',
	'author': 'ITGRUPO',
	'depends': ['account_fields_it','account_report_menu_it'],
	'version': '1.0',
	'description':"""
	- Campos y funcionalidad para Flujo de Caja
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/security.xml',
		'security/ir.model.access.csv',
		'views/account_account.xml',
		'views/account_cash_flow.xml',
		'views/account_cash_flow_book.xml',
		'wizard/account_cash_flow_rep.xml'
	],
	'installable': True
}