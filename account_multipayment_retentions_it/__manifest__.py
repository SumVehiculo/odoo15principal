# -*- encoding: utf-8 -*-
{
	'name': 'Retenciones en pagos multiples',
	'category': 'account',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['account_multipayment_advance_it'],
	'version': '1.0',
	'description':"""
	Aplicacion de Retenciones en pagos multiples
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'views/account_main_parameter.xml',
		'views/multipayment_advance_it.xml',
		#'wizard/get_invoices_multipayment_wizard.xml'
		],
	'installable': True
}
