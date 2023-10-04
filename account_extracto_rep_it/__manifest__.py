# -*- encoding: utf-8 -*-
{
	'name': 'Reporte EXTRACTOS BANCARIOS',
	'category': 'account',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['account_base_it','report_tools'],
	'version': '1.0',
	'description':"""
	Reporte en Excel para Extractos Bancarios
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'views/account_bank_statement.xml'
		],
	'installable': True,
	'license': 'LGPL-3'
}
