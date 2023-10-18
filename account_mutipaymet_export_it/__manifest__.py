# -*- encoding: utf-8 -*-
{
	'name': 'Exportar Pagos al BCP',
	'category': 'account',
	'author': 'ITGrupo',
	'depends': ['account_multipayment_advance_it','account_menu_other_configurations'],
	'version': '1.0',
	'description':"""Exportar pagos al BCP deacuerdo a su formato""",
	'auto_install': False,
	'demo': [],
	'data':	['views/multipaymet_exportbcp_it_view.xml',
             'security/ir.model.access.csv',
			],
	'installable': True
}