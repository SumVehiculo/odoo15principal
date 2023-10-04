# -*- encoding: utf-8 -*-
{
	'name': 'Entregas Gratuitas Stock',
	'category': 'stock',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['kardex_account_journal_entry'],
	'version': '1.0',
	'description':"""
	- Reporte de Entregas Gratuitas
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/ir.model.access.csv',
		'wizards/surrender_free_wizard.xml',
		'views/account_main_parameter.xml',
		'views/surrender_free_book.xml',
		'views/surrender_free_concepts.xml'
	],
	'installable': True,
	'license': 'LGPL-3'
}
