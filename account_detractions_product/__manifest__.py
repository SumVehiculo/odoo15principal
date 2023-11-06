# -*- encoding: utf-8 -*-
{
	'name': 'Detracciones Automáticas',
	'category': 'account',
	'author': 'ITGRUPO, Sebastian Moises Loraico Lopez',
	'depends': ['account_fields_it','account_invoice_detracciones_it'],
	'version': '1.0',
	'description':"""
		Genera la Detraccion automatica segun el producto
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		
		'views/account_main_parameter.xml',
		'views/product_template.xml'
	],
	'installable': True,
	'license': 'LGPL-3'
}
