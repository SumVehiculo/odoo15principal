# -*- encoding: utf-8 -*-
{
	'name': 'Importador Tarifa Compra',
	'category': 'purchase',
	'author': 'ITGRUPO',
	'depends': ['base','stock','account_accountant','account','purchase'],
	'version': '1.0',
	'description':"""
		Importador Tarifa Compra
	""",
	'auto_install': False,
	'demo': [],
	'data': [
		'security/ir.model.access.csv',
        'security/tarifa_compra_import_security.xml',
        'data/attachment_sample.xml',
        'views/tarifa_compra_import_view.xml',        
    ],
	'installable': True
}