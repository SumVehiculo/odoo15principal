# -*- encoding: utf-8 -*-
{
	'name': 'Importacion Actualizar Analiticos IT',
	'category': 'account',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['account_base_import_it'],
	'version': '1.0',
	'description':"""
		Importacion Inforest IT, actualizar diario analitico
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/ir.model.access.csv',
		'wizard/importacion_view.xml'
		],
	'installable': True
}
