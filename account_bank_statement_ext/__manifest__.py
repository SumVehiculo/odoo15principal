# -*- coding: utf-8 -*-
{
    'name': 'Funcionalidad Extracto Bancario',
    'summary': """ Extracto Bancario Funcionalidades """,
    'author': 'ITGRUPO, Sebastian Moises Loraico Lopz',
    'depends': ['account_bank_statement_reconcile', ],
    "data": [
        "views/account_bank_statement_views.xml"
    ],
    
    'application': True,
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
