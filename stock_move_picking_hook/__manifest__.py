# -*- encoding: utf-8 -*-
{
	'name': 'Stock Move Picking Hook',
	'category': 'Kardex',
	'author': 'ITGRUPO',
	'depends': ['sale'],
	'version': '1.0',
	'description':"""
	Modulo para enganchar albaranes con su respectiva factura
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/ir.model.access.csv',
		'views/sale_advance_payment_inv.xml',
			],
	'installable': True
}