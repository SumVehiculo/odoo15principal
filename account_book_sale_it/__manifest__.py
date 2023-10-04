# -*- encoding: utf-8 -*-
{
	'name': 'Reporte REGISTRO DE VENTAS',
	'category': 'account',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['account_report_menu_it'],
	'version': '1.0',
	'description':"""
		Generar Reportes para REGISTRO DE VENTAS
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/ir.model.access.csv',
		'wizards/account_book_sale_wizard.xml',
		'views/account_book_sale_view.xml'
	],
	'installable': True,
	'license': 'LGPL-3'
}
