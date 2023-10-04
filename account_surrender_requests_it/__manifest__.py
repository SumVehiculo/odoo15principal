# -*- encoding: utf-8 -*-
{
	'name': 'Solicitudes de Entrega IT',
	'category': 'account',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['account_fields_it','account_menu_rendiciones_it','account_bank_statement_reconcile'],
	'version': '1.0',
	'description':"""
	- Solicitudes de Entrega
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/security.xml',
		'security/ir.model.access.csv',
		'views/render_type_document.xml',
		'views/render_main_parameter.xml',
		'views/account_bank_statement.xml',
		'views/account_surrender_requests_it.xml'
		],
	'installable': True,
	'license': 'LGPL-3'
}