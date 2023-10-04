# -*- encoding: utf-8 -*-
{
	'name': 'Saltos de Voucher segun numeracion',
	'category': 'account',
	'author': 'ITGRUPO-Glenda Julia',
	'depends': ['account_consistencia_rep_it','report_tools'],
	'version': '1.0',
	'description':"""
	- Reporte para verificar saltos de numeración en cheques
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/ir.model.access.csv',
		'wizard/check_voucher_skip_detection_wizard.xml'
	],
	'installable': True
}