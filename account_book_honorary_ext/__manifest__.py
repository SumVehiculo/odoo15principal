# -*- encoding: utf-8 -*-
{
	'name': 'Reporte LIBRO HONORARIOS Extendido',
	'category': 'account',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['account_book_honorary_it','account_sunat_it'],
	'version': '1.0',
	'description':"""
		- Cambia nombre en reporte Honorarios 
        - Agrega Tipo de Recibo de Honorarios en Facturas
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'views/account_move.xml',
		'views/account_book_honorary_view.xml'
	],
	'installable': True,
	'license': 'LGPL-3'
}
