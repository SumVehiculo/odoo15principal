# -*- coding: utf-8 -*-

{
	'name': 'Importar Cuentas Bancarias IT',
	'category': 'Base',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['contacts','account_fields_it','popup_it','account_base_import_it'],
	'version': '1.0',
	'description':"""
	- Importar Cuentas Bancarias
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'data/attachment_sample.xml',
		'security/ir.model.access.csv',
		'views/import_partner_bank_it.xml',
	],
	'installable': True,
	'license': 'LGPL-3'
}
