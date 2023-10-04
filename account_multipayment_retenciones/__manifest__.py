# -*- encoding: utf-8 -*-
{
	'name': 'Retenciones en PM',
	'category': 'account',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['account_multipayment_advance_it','account_sunat_it'],
	'version': '1.0',
	'description':"""
	- TXT Retenciones en pagos multiples
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'wizards/account_sunat_wizard.xml',
		'views/account_main_parameter.xml',
		'views/multipayment_advance_it.xml'
	],
	'installable': True,
	'license': 'LGPL-3'
}
