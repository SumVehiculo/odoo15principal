# -*- encoding: utf-8 -*-
{
	'name': 'Importar Facturas IT',
	'category': 'account',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['account_base_import_it','currency_rate_personalize'],
	'version': '1.0',
	'description':"""
	Sub-menu para importar Facturas Cliente/Proveedor
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'data/attachment_sample.xml',
		'security/security.xml',
		'security/ir.model.access.csv',
		'views/import_invoice_it.xml'
		],
	'installable': True,
	'license': 'LGPL-3'
}