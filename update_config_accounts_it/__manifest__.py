# -*- encoding: utf-8 -*-
{
	'name': 'Actualizar cuentas predeterminadas',
	'category': 'account',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['account','account_menu_other_configurations','popup_it'],
	'version': '1.0',
	'description':"""
		Actualizar cuentas predeterminadas por compañía
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/ir.model.access.csv',
		'wizard/update_default_accounts_wizard.xml'
	],
	'installable': True,
	'license': 'LGPL-3'
}
