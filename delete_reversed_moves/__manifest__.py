# -*- encoding: utf-8 -*-
{
	'name': 'Eliminar de Asientos de Reversion para Tipo de Cambio',
	'category': 'account',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['account_base_it','popup_it'],
	'version': '1.0',
	'description':"""
		- Eliminar de Asientos de Reversion para Tipo de Cambio
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/ir.model.access.csv',
		'wizard/delete_reversed_move.xml'
	],
	'installable': True,
	'license': 'LGPL-3'
}