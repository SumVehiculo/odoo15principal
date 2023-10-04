# -*- encoding: utf-8 -*-
{
	'name': 'Account Credit Note',
	'category': 'account',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['account_fields_it','l10n_latam_invoice_document_it','account_debit_note'],
	'version': '1.0',
	'description':"""
	Funcionalidades para Notas de Credito
	""",
	'auto_install': False,
	'demo': [],
	'data':	['views/account_move_reversal.xml',
			 'views/account_move.xml'],
	'installable': True,
	'license': 'LGPL-3'
}