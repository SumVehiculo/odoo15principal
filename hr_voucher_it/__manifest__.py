# -*- encoding: utf-8 -*-
{
	'name': 'Hr Voucher IT',
	'category': 'hr',
	'author': 'ITGRUPO-HR',
	'depends': ['hr_fields_it'],
	'version': '1.0',
	'description':"""
	Modulo para Boletas de pago en Nominas
	""",
	'auto_install': False,
	'demo': [],
	'data':	['views/hr_main_parameter.xml',
			 'views/hr_payslip.xml',
			 'views/hr_payslip_run.xml'],
	'installable': True,
	'license': 'LGPL-3',
}
