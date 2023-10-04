# -*- encoding: utf-8 -*-
{
	'name': 'Detracciones',
	'category': 'account',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['account_fields_it'],
	'version': '1.0',
	'description':"""
	Generar Detracciones en Facturas de Clientes y Proveedores
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
			'security/ir.model.access.csv',
			'views/account_detractions_wizard.xml',
			'views/account_move.xml'
	],
	'installable': True,
	'license': 'LGPL-3'
}
