# -*- encoding: utf-8 -*-
{
	'name': 'Reporte AUXILIAR DE BANCOS',
	'category': 'account',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['account_report_menu_it'],
	'version': '1.0',
	'description':"""
		Generar Reportes para AUXILIAR DE BANCOS
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/ir.model.access.csv',
		'wizards/account_bank_rep.xml',
		'views/account_bank_book.xml'
	],
	'installable': True,
	'license': 'LGPL-3'
}
