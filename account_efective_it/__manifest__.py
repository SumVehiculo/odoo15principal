# -*- encoding: utf-8 -*-
{
	'name': 'Reporte FLUJO EFECTIVO',
	'category': 'account',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['account_report_menu_it'],
	'version': '1.0',
	'description':"""
	Reporte de Flujo de Efectivo
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
			'security/ir.model.access.csv',
			'wizards/efective_flow_wizard.xml'
			],
	'installable': True,
	'license': 'LGPL-3'
}