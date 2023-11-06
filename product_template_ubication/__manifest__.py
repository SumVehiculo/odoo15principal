# -*- coding: utf-8 -*-
{
	'name': "Agregar pestaña de ubicacion en productos",
	'author': 'ITGRUPO, Alessandro Pelayo Mollocondo Medrano',
	'category': 'Purchases',
	'description': """Agregar pestaña de ubicacion en productos para que se pueda observar la ubicacion teorica""",
	'version': '1.0',
	'summary': 'Modificaciones personalizadas para product',
	'depends': ['stock'],
	'data': [
		'security/ir.model.access.csv',
		'views/add_new_ubication.xml',
		'views/casepack.xml',
		'views/ubication.xml',
	],
	'demo': [],
	'installable': True,
	'application': False,
	'license': 'LGPL-3',
}