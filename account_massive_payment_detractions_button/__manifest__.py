# -*- encoding: utf-8 -*-
{
	'name': 'Txt Detracciones Boton',
	'category': 'account',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['account_massive_payment_detractions_it'],
	'version': '1.0',
	'description':"""
	- Generar Pago Masivo de Detracciones en Base a Pagos Multiples
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/security.xml',
		'views/multipayment_advance_it.xml',
	],
	'installable': True,
	'license': 'LGPL-3'
}