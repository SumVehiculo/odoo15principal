# -*- encoding: utf-8 -*-
{
	'name': 'Kardex Save Period IT Updated',
	'category': 'Kardex',
	'author': 'ITGRUPO',
	'depends': ['stock','kardex_save_period_tabla','kardex_save_period_final','kardex_actualizar_transferencia_it'],
	'version': '1.0',
	'description':"""
	- Kardex almacenado mensual Mejoras
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'views/kardex.xml',
		'views/ir.model.access.csv',
		],
	'installable': True
}