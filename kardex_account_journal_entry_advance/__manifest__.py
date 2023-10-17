# -*- encoding: utf-8 -*-
{
	'name': 'Detalle de Movimientos en Asientos Contables',
	'category': 'stock',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['account_fields_it','kardex_fields_it','kardex_fisico_it','kardex_valorizado_cuentas_contables_it','kardex_account_journal_entry'],
	'version': '1.0',
	'description':"""
	- Detalle de Movimientos en Asientos Contables
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'SQL.sql',
		'security/ir.model.access.csv',
		'wizards/kardex_entry_income_wizard.xml',
		'wizards/kardex_entry_outcome_wizard.xml',
		'views/account_main_parameter.xml',
		'views/kardex_entry_income_book.xml',
		'views/kardex_entry_outcome_book.xml',
		'views/type_operation_kardex.xml'
	],
	'installable': True,
	'license': 'LGPL-3'
}
