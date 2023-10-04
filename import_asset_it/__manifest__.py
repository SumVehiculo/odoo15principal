# -*- encoding: utf-8 -*-
{
	'name': 'Importar Activos IT',
	'category': 'account',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['account_fields_it','account_base_import_it','om_account_asset'],
	'version': '1.0',
	'description':"""
	- Se crea el menú Importar Activos
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'data/attachment_sample.xml',
		'security/ir.model.access.csv',
		'wizard/import_asset_wizard.xml'
		],
	'installable': True,
	'license': 'LGPL-3'
}
