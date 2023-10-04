# -*- encoding: utf-8 -*-
{
	'name': 'Reporte Flujo de Caja Avanzado',
	'category': 'account',
	'author': 'ITGRUPO',
	'depends': ['account_cash_flow_rep'],
	'version': '1.0',
	'description':"""
	- Nuevo Reporte para Flujo de Caja
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/security.xml',
		'security/ir.model.access.csv',
		'views/account_main_parameter.xml',
		'views/account_cash_flow_book_advance.xml',
		'wizard/account_cash_flow_rep_advance.xml'
	],
	'installable': True
}