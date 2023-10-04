# -*- encoding: utf-8 -*-
{
	'name': 'Reporte PERCEPCIONES',
	'category': 'account',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['account_report_menu_it'],
	'version': '1.0',
	'description':"""
		Generar Reportes para PERCEPCIONES
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/ir.model.access.csv',
		'wizards/account_book_perception_wizard.xml',
		'views/account_book_perception.xml',
		'views/account_book_perception_sp.xml'
	],
	'installable': True,
	'license': 'LGPL-3'
}
