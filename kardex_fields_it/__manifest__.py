# -*- encoding: utf-8 -*-
{
	'name': 'Kardex Fields',
	'category': 'Kardex',
	'author': 'ITGRUPO-OWM',
	'depends': ['analytic','stock','account_base_it'],
	'version': '1.0',
	'description':"""
	- Agregar campos para Cuentas Analiticas en Albaranes
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/ir.model.access.csv',
			'views/stock_picking.xml','assets.xml'
		],
	'installable': True
}
