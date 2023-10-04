# -*- encoding: utf-8 -*-
{
	'name': 'Hr Fifth Category',
	'category': 'hr',
	'author': 'ITGRUPO-HR',
	'depends': ['hr_fields_it', 'hr_social_benefits', 'account_accountant'],
	'version': '1.0',
	'description':"""
	Modulo para el calculo de Quinta Categoria
	""",
	'auto_install': False,
	'demo': [],
	'data':	['security/security.xml',
			 'security/ir.model.access.csv',
			 'wizard/hr_employee_excluidos_wizard.xml',
			 'views/account_fiscal_year.xml',
			 'views/hr_contract.xml',
			 'views/hr_fifth_category.xml',
			 'views/hr_main_parameter.xml'
			],
	'installable': True,
	'license': 'LGPL-3',
}
