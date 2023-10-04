# -*- encoding: utf-8 -*-
{
	'name': 'Menu Rendiciones',
	'category': 'account',
	'author': 'ITGRUPO, Glenda Julia Merma Mayhua',
	'depends': ['account_accountant','account_fields_it','account_treasury_it','import_invoice'],
	'version': '1.0',
	'description':"""
        MENU DE REPORTES PARA LOCALIZACION CONTABLE
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/security.xml',
		'security/ir.model.access.csv',
        'views/product_product.xml',
        'views/account_bank_statement.xml',
        'views/import_invoice_it.xml',
        'views/menu_views.xml'
    ],
	'installable': True
}
