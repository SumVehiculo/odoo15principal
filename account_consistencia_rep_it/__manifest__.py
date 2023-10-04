# -*- encoding: utf-8 -*-
{
	'name': 'Reportes CONSISTENCIAS',
	'category': 'account',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['account_report_menu_it'],
	'version': '1.0',
	'description':"""
		Generar Reportes para CONSISTENCIA FLUJO EFECTIVO
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/ir.model.access.csv',
		'wizards/account_consistency_rep.xml',
		'views/account_con_efective_book.xml'
	],
	'installable': True,
	'license': 'LGPL-3'
}
