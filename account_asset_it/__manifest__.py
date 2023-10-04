# -*- encoding: utf-8 -*-
{
	'name': 'Reporte GASTOS DIFERIDOS',
	'category': 'account',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['account_asset','account_fields_it'],
	'version': '1.0',
	'description':"""
		Generar Reportes para GASTOS DIFERIDOS
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/ir.model.access.csv',
		'wizards/account_deferred_expense_wizard.xml',
		'views/account_deferred_expense_view.xml',
		'views/account_asset.xml'
	],
	'installable': True,
	'license': 'LGPL-3'
}
