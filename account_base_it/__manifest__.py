# -*- encoding: utf-8 -*-
{
	'name': 'Account Base IT',
	'category': 'account',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['l10n_latam_base','popup_it','account_accountant','l10n_latam_invoice_document','l10n_pe'],
	'version': '1.0',
	'description':"""
	Creacion de Catalogos y Tablas
		-Medio de Pago SUNAT
		-Tipos Estados Financieros
		-Flujo de Efectivo
		-Patrimonio Neto
		-Periodos
		-Flujo de Caja
		-Series de Comprobantes
		-Porcentajes de Detraccion
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
			'security/security.xml',
			'security/ir.model.access.csv',
			'data/einvoice_catalog_payment.xml',
			'data/account_type_it.xml',
			'data/account_efective_type.xml',
			'data/account_patrimony_type.xml',
			'views/account_cash_flow.xml',
			'views/account_efective_type.xml',
			'views/account_main_parameter.xml',
			'views/account_patrimony_type.xml',
			'views/account_period.xml',
			'views/account_type_it.xml',
			'views/detractions_catalog_percent.xml',
			'views/einvoice_catalog_06.xml',
			'views/einvoice_catalog_payment.xml',
			'views/it_invoice_serie.xml',
			'views/menu_items.xml',
			],
	'installable': True,
	'license': 'LGPL-3'
}
