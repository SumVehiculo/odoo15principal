# -*- encoding: utf-8 -*-
{
	'name': 'Importador Tarifa Venta',
	'category': 'sale',
	'author': 'ITGRUPO',
	'depends': ['base','stock','account_accountant','account','sale'],
	'version': '1.0',
	'description':"""
		Importador Tarifa Venta
	""",
	'auto_install': False,
	'demo': [],
	'data': [
		'security/ir.model.access.csv',
        'security/tarifa_import_security.xml',
        'data/attachment_sample.xml',
        'views/tarifa_import_view.xml',        
    ],
	'installable': True
}