# -*- encoding: utf-8 -*-
{
	'name': 'Control en Ordenes de Produccion',
	'category': 'account',
	'author': 'ITGRUPO',
	'depends': ['mrp', 'kardex_fisico_it','kardex_fields_it'],
	'version': '1.0',
	'description':"""
	Modulo para agregar Raise en Ordenes de Produccion y algunos campos.
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
			'security/security.xml',
			'views/mrp_kardex.xml'],
	'installable': True
}
