# -*- encoding: utf-8 -*-
{
	'name': 'Stock Account IT',
	'category': 'stock,account',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['stock_account','account_base_it'],
	'version': '1.0',
	'description':"""
	Inventario y Contabilidad:
	- Categorias Productos
	- Catalogos de Inventarios Sunat
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
			'security/ir.model.access.csv',
			'data/stock_catalog_05.xml',
			'data/stock_catalog_06.xml',
			'views/stock_catalog_05.xml',
			'views/stock_catalog_06.xml',
			'views/product_category.xml',
			'views/uom_uom.xml',
			'views/menu_items.xml',
			],
	'installable': True,
	'license': 'LGPL-3'
}
