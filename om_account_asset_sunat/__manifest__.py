# -*- encoding: utf-8 -*-
{
	'name': 'PLE Activos en SUNAT',
	'category': 'account',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['om_account_asset','account_sunat_it'],
	'version': '1.0',
	'description':"""
	PLE Activos 7.1 y 7.4 en menu SUNAT/PLES
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'wizard/account_sunat_wizard.xml'
		],
	'installable': True,
	'license': 'LGPL-3'
}
