# -*- encoding: utf-8 -*-
{
	'name': 'Monto en Moneda Extranjera',
	'category': 'account',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['account_base_currency_dolars_it','l10n_pe_currency_rate','exchange_diff_config_it'],
	'version': '1.0',
	'description':"""
	- Monto en Moneda Extranjera
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/security.xml',
		'security/ir.model.access.csv',
		'views/account_main_parameter.xml',
		#'views/account_purchase_book.xml',
		#'views/account_sale_book.xml',
		#'views/account_balance_period_usd.xml',
		#'views/account_exchange_usd_book.xml',
		#'views/account_exchange_document_usd_book.xml',
		#'views/f1_register_usd.xml',
		#'views/f1_balance_usd.xml',
		'views/account_journal_usd_book.xml',
		#'views/account_des_detail_usd_book.xml',
		'views/menu_views.xml',
		'views/adjustment_account_account.xml',
		#'wizards/account_balance_period_usd_rep.xml',
		#'wizards/account_purchase_rep.xml',
		#'wizards/account_destinos_usd_wizard.xml',
		#'wizards/account_des_detail_usd_rep.xml',
		#'wizards/account_sale_rep.xml',
		#'wizards/financial_situation_wizard.xml',
		#'wizards/function_result_wizard.xml',
		#'wizards/nature_result_wizard.xml',
		'wizards/update_rate_dolars_wizard.xml',
		'wizards/account_journal_usd_rep.xml',
		'wizards/update_uneven_entries_wizard.xml',
		#'wizards/account_exchange_usd_rep.xml',
		#'wizards/account_exchange_document_usd_rep.xml',
		'wizards/account_different_tc_wizard.xml',
		'wizards/account_wrong_sign_wizard.xml',
		'SQL.sql'
	],
	'installable': True
}