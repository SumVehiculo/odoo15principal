# -*- encoding: utf-8 -*-
{
	'name': 'Reporte LIBRO MAYOR',
	'category': 'account',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['account_report_menu_it'],
	'version': '1.0',
	'description':"""
		Generar Reportes para LIBRO MAYOR
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/ir.model.access.csv',
		'wizards/account_book_ledger_wizard.xml',
		'views/account_book_ledger_view.xml'
	],
	'installable': True,
	'license': 'LGPL-3'
}
