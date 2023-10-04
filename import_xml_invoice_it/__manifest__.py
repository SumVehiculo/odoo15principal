# -*- encoding: utf-8 -*-
{
	'name': 'Import XML Invoice',
	'category': 'account',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['account_fields_it','account_move_autofill','account_base_import_it','currency_rate_personalize','account_constraint_invoices_it'],
	'version': '1.0',
	'description':"""
	Modulo para importar Facturas desde XML
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
        'security/security.xml',
		'security/ir.model.access.csv',
		'views/import_xml_invoice_it.xml',
		'views/account_tax.xml'
	],
	'installable': True,
	'license': 'LGPL-3'
}