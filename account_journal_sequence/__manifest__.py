# -*- encoding: utf-8 -*-
{
	'name': 'Generacion de Secuencias para Diarios',
	'category': 'account',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['account_fields_it','account_menu_other_configurations'],
	'version': '1.0',
	'description':"""
	Generacion de Secuencias para Diarios
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
			'security/ir.model.access.csv',
			'views/account_journal.xml',
			'wizards/account_sequence_journal_wizard.xml',
			'wizards/sequence_wizard.xml'
			],
	'installable': True,
	'license': 'LGPL-3'
}
