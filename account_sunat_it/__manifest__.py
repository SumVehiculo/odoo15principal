# -*- encoding: utf-8 -*-
{
	'name': 'Reporte PLE SUNAT',
	'category': 'account_sunat',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['account_base_sunat_it','popup_it','report_tools'],
	'version': '1.0',
	'description':"""
		- Nuevo menu SUNAT para generar PLEs
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/ir.model.access.csv',
		'wizards/account_sunat_wizard.xml'
	],
	'installable': True,
	'license': 'LGPL-3'
}