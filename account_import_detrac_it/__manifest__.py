# -*- encoding: utf-8 -*-
{
	'name': 'Importar Detracciones IT',
	'category': 'account',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['account_fields_it','account_base_import_it'],
	'version': '1.0',
	'description':"""
	- Se crea el menú Actualizar Detracciones
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'data/attachment_sample.xml',
		'security/ir.model.access.csv',
		'wizard/import_detrac_wizard.xml'
		],
	'installable': True,
	'license': 'LGPL-3'
}
