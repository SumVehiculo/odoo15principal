# -*- encoding: utf-8 -*-
{
	'name': 'Reporte extractos bancarios',
	'category': 'account',
	'author': 'ITGRUPO,Sebastian Moises Loraico Lopez',
	'depends': ['account_treasury_it','account_fields_it','popup_it'],
	'version': '1.0',
	'description':"""
	
    Reporte extractos bancarios
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
        'security/ir.model.access.csv',
		'wizard/report_extracto_bancarios.xml'
        ],
	'installable': True,
	'license': 'LGPL-3'
}
