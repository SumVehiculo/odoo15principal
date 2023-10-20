# -*- encoding: utf-8 -*-
{
	'name': 'PRESTAMOS',
	'category': 'account',
	'author': 'ITGRUPO, Moises L',
	'depends': ['account_treasury_it','mail','account_multipayment_supplier_retentions'],
	'version': '1.0',
	'description':"""
		Modulo de Prestamos
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
        'data/attachment_sample.xml',
        'security/security.xml',
		'security/ir.model.access.csv',
        'views/bank_loans.xml',
		'wizard/bank_loans_lines_import.xml',
		
	],
	'installable': True,
    'application': False,
	'license': 'LGPL-3'
}


