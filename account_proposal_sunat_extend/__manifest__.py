# -*- encoding: utf-8 -*-
{
	'name': 'Propuesta Sunat_ODOO',
	'category': 'account',
	'author': 'ITGRUPO, Sebastian Moises Loraico Lopez',
	'depends': ['account_sunat_sire_it'],
	'version': '1.0',
    'license': 'LGPL-3',
	'description':"""
		Compara propuesta odoo y propuesta sunat
	""",
    'application': False,
	'auto_install': False,
	'demo': [],
	'data':	[
		'wizard/account_sunat_rep.xml',		
	],
	'installable': True
}

