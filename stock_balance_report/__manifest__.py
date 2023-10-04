# -*- encoding: utf-8 -*-
{
	'name': 'Stock Balance Report',
	'category': 'stock',
	'author': 'ITGRUPO',
	'depends': ['stock', 'kardex_fisico_it', 'sale'],
	'version': '1.0',
	'description':"""
	Reporte de Saldos
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/security.xml',
		'security/ir.model.access.csv',
		'views/stock_balance_report.xml'
	],
	'installable': True
}
