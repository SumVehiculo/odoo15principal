# -*- encoding: utf-8 -*-
{
	'name': 'Existencias por Recibir IT',
	'category': 'Kardex',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['landed_cost_it'],
	'version': '1.0',
	'description':"""
	- Existencias por Recibir
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'views/account_main_parameter.xml',
		'views/landed_cost_it.xml',
		'views/product_category.xml'
		],
	'installable': True,
	'license': 'LGPL-3'
}