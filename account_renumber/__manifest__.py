# -*- encoding: utf-8 -*-
{
	'name': 'Account Renumber',
	'category': 'account',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['account','account_fields_it'],
	'version': '1.0',
	'description':"""
	Modulo para renumerar Asientos Contables
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
			'security/ir.model.access.csv',
			'wizard/wizard_renumber_view.xml'],
	'installable': True,
	'license': 'LGPL-3'
}
