# -*- encoding: utf-8 -*-
{
	'name': 'Cierre Gastos Vinculados IT',
	'category': 'Kardex',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['landed_cost_it'],
	'version': '1.0',
	'description':"""
	- Cierre Gastos Vinculados
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/security.xml',
		'security/ir.model.access.csv',
		'views/landed_cost_closing_it.xml',
		'views/landed_cost_it.xml'
		],
	'installable': True,
	'license': 'LGPL-3'
}