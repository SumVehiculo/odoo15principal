# -*- encoding: utf-8 -*-
{
	'name': 'Gastos Vinculados IT',
	'category': 'Kardex',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['account','purchase_stock','account_fields_it','l10n_pe_currency_rate','kardex_valorado_it'],
	'version': '1.0',
	'description':"""
	- Gastos Vinculados Localizacion Contable 13
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/security.xml',
		'security/ir.model.access.csv',
		'views/landed_cost_it.xml',
		'views/landed_cost_it_type.xml',
		'views/account_move.xml',
		'views/account_move_line.xml',
		'views/purchase_order.xml',
		'views/purchase_order_line.xml',
		'views/product_template.xml',
		'views/stock_picking.xml',
		'wizard/get_landed_purchases_wizard.xml',
		'wizard/get_landed_invoices_wizard.xml'
		],
	'installable': True,
	'license': 'LGPL-3'
}