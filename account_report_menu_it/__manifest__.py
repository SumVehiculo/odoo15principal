# -*- encoding: utf-8 -*-
{
	'name': 'Menu Reportes de Localizacion Contable',
	'category': 'account',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['account_fields_it','report_tools'],
	'version': '1.0',
	'description':"""
	- MENU DE REPORTES PARA LOCALIZACION CONTABLE
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'libro_contables_peruanos.sql',
		'cuentas_corrientes.sql',
		'estados_financieros.sql',
		'views/account_report_menu_it.xml'
	],
	'installable': True,
	'license': 'LGPL-3'
}
