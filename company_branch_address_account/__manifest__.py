# -*- coding: utf-8 -*-
{
    'name': 'Company Branch Address in Account',
    'version': '14.0.1.0.0',
    'category': 'Account',
    'author': 'Conflux',
    'description': "",
    'depends': ['company_branch_address','account'],
    'data': [
        'security/res_company_branch_address_security.xml',
        'views/account_move_view.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'OPL-1',
}