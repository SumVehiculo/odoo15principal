# -*- encoding: utf-8 -*-
{
	'name': 'Campos Activos fijos',
	'category': 'account',
	'author': 'ITGRUPO,Sebastian Moises Loraico Lopez',
	'depends': ['account','om_account_asset','import_asset_it'],
	'version': '1.0',
	'description':"""
		Agrega nuevos campos para los activos fijos en contabilidad
	""",
	'auto_install': False,
	'demo': [],
	'data':	[	
        'data/attachment_sample.xml',	
		'views/account_asset_asset.xml'
	],
	'installable': True
}
