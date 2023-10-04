# -*- encoding: utf-8 -*-
{
	'name': 'Account Fields IT',
	'category': 'account',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['account_base_it','account_batch_payment','account_budget'],
	'version': '1.0',
	'description':"""
	Nuevos campos para el BO
	Tablas:
	- Etiquetas de Cuenta
	- Cuentas
	- Cuentas Analiticas
	- Lotes de Pago
	- Grupos de Cuentas
	- Diarios
	- Asientos/Facturas
	- Pagos
	- Tipos de Documento
	- Monedas
	- Partners
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
			'views/account_account_tag.xml',
			'views/account_account.xml',
			'views/account_analytic_account.xml',
			'views/account_bank_statement.xml',
			'views/account_batch_payment.xml',
			'views/account_fiscal_year.xml',
			'views/account_group.xml',
			'views/account_journal.xml',
			'views/account_move_line.xml',
			'views/account_move.xml',
			'views/account_payment.xml',
			'views/l10n_latam_document_type_view.xml',
			'views/res_currency.xml',
			'views/res_partner_bank.xml',
			'views/res_partner.xml',
			],
	'installable': True,
	'license': 'LGPL-3'
}
