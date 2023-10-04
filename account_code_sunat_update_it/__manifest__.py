# -*- encoding: utf-8 -*-
{
	'name': 'Importador Codigo Sunat',
	'category': 'account',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['account_base_sunat_it','account_fields_it'],
	'version': '1.0',
	'description':"""
	Generador de Codigo Sunat
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/ir.model.access.csv',
		'wizard/wizard_code_sunat_update.xml',
		'views/account_code_sunat_table.xml'
		],
	'installable': True,
	'license': 'LGPL-3'
}
