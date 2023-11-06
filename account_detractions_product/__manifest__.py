# -*- encoding: utf-8 -*-
{
	'name': 'Detracciones Automáticas',
	'category': 'account',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['account_report_menu_it','account_consistencia_rep_it'],
	'version': '1.0',
	'description':"""
		Genera la Detraccion automatica segun el producto
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		
		'views/account_main_parameter.xml',
		'views/account_des_move.xml'
	],
	'installable': True,
	'license': 'LGPL-3'
}
