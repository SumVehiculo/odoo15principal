# -*- encoding: utf-8 -*-
{
	'name': 'Reporte PLE SUNAT',
	'category': 'account_sunat',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['account_report_menu_it','l10n_pe_currency_rate'],
	'version': '1.0',
	'description':"""
		- Nuevo menu SUNAT para generar PLEs
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/security.xml',
		'security/ir.model.access.csv',
		'views/account_sunat_menu.xml'
	],
	'installable': True,
	'license': 'LGPL-3'
}