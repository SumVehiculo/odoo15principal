# -*- encoding: utf-8 -*-
{
	'name': 'Hr Advances and Loans',
	'category': 'hr',
	'author': 'ITGRUPO-HR',
	'depends': ['hr_fields_it', 'hr_social_benefits','hr_leave_it'],
	'version': '1.0',
	'description':"""
	Modulo de Adelantos y Prestamos
	""",
	'auto_install': False,
	'demo': [],
	'data':	['security/security.xml',
			 'security/ir.model.access.csv',
			 'data/hr_advance_type_data.xml',
			 'data/hr_loan_type_data.xml',
			 'views/hr_advance.xml',
			 'views/hr_loan.xml',
			 'views/hr_gratification.xml',
			 'views/hr_cts.xml',
			 'views/hr_vacation.xml',
			 'views/hr_liquidation.xml',
			 'views/hr_main_parameter.xml',
			 'views/hr_payslip.xml',
			 'views/hr_payslip_run.xml',
			 'wizards/report_cuenta_corriente.xml'],
	'installable': True,
	'license': 'LGPL-3',
}
