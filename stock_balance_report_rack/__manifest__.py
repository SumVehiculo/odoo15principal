# -*- encoding: utf-8 -*-
{
	'name': 'Stock Balance Report rack',
	'category': 'stock',
	'author': 'ITGRUPO',
	'depends': ['stock_balance_report','stock_balance_report_lote','product_template_ubication'],
	'version': '1.0',
	'description':"""
	Reporte de Saldos rack
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'views/stock_balance_report.xml'
	],
	'installable': True
}
