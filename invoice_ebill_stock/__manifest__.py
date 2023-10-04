# -*- encoding: utf-8 -*-
{
	'name': 'Invoice Ebill Stock',
	'category': 'account',
	'author': 'ITGRUPO',
	'depends': ['sale_stock','invoice_ebill_stock_no_obligatorio','account','stock'],
	'version': '1.0',
	'description':"""
	Agregar información a la factura.
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
			'security/security.xml',
			'views/mrp_kardex.xml'],
	'installable': True
}
