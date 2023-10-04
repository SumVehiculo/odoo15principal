# -*- encoding: utf-8 -*-
{
	'name': 'Generador de CUOs',
	'category': 'account_sunat',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['account_fields_it','popup_it','account_base_sunat_it'],
	'version': '1.0',
	'description':"""
		- Nuevo menu para generar CUOS para PLEs
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/ir.model.access.csv',
		'wizards/cuo_generator.xml'
	],
	'installable': True,
	'license': 'LGPL-3'
}