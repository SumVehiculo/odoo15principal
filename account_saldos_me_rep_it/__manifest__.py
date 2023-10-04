# -*- encoding: utf-8 -*-
{
	'name': 'Reporte Saldos Moneda Extranjera',
	'category': 'account',
	'author': 'ITGRUPO',
	'depends': ['account_report_menu_it'],
	'version': '1.0',
	'description':"""
		Generar Reportes para Saldos Moneda Extranjera
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/ir.model.access.csv',
		'wizards/account_saldos_me_rep.xml',
		'views/account_saldos_me_book.xml',
		'SQL.sql'
	],
	'installable': True
}
