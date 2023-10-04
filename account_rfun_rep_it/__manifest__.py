# -*- encoding: utf-8 -*-
{
	'name': 'Reporte RESULTADO POR FUNCION',
	'category': 'account',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['account_report_menu_it'],
	'version': '1.0',
	'description':"""
	Reporte Resultado por Funcion
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
			'security/ir.model.access.csv',
			'wizards/function_result_wizard.xml'
			],
	'installable': True,
	'license': 'LGPL-3'
}