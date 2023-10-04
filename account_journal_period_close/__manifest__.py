# -*- encoding: utf-8 -*-
{
	'name': 'Cierre de Periodo',
	'category': 'account',
	'author': 'ITGRUPO,Glenda Julia Merma Mayhua',
	'depends': ['account_base_it'],
	'version': '1.0',
	'description':"""
	Sub-menu con Tabla de Cierre de Periodo
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/security.xml',
		'security/ir.model.access.csv',
		'views/account_journal_period.xml'
		],
	'installable': True,
	'license': 'LGPL-3'
}
