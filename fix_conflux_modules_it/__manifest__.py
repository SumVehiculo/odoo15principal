# -*- encoding: utf-8 -*-
{
	'name': 'Fix Conflux',
	'category': 'account',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['l10n_pe_edi_extended','l10n_pe_edi_extended_detraction','l10n_pe_edi_extended_transportrefs','account_fields_it'],
	'version': '1.0',
	'description':"""
	- Fix modulos de Conflux
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'views/account_move_reversal.xml',
		'views/account_move.xml'
	],
	'installable': True
}
