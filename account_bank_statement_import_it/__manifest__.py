# -*- encoding: utf-8 -*-
{
	'name': 'Importador de Lineas de Extractos Bancarios',
	'category': 'account',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['account_fields_it'],
	'version': '1.0',
	'description':"""
	Modulo para importar Lineas de Extractos Bancarios
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'data/attachment_sample.xml',
		'security/ir.model.access.csv',
		'views/account_bank_statement.xml',
        'wizard/import_statement_line_wizard.xml',
		],
	'installable': True
}
