# -*- encoding: utf-8 -*-
{
	'name': 'Importador Productos',
	'category': 'stock',
	'author': 'ITGRUPO',
	'depends': ['base','stock','account_accountant','account'],
	'version': '1.0',
	'description':"""
		Importador Productos
	""",
	'auto_install': False,
	'demo': [],
	'data': [
		'security/ir.model.access.csv',
        'security/product_import_security.xml',
        'data/attachment_sample.xml',
        'views/product_import_view.xml',        
    ],
	'installable': True
}