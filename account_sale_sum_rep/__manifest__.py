# -*- coding: utf-8 -*-
{
    'name': 'PLANTILLA DE VENTAS FINANCIERAS',
    'summary': """ PLANTILLA DE VENTAS FINANCIERAS """,
    'author': 'ITGRUPO, Sebastian Moises Loraico Lopez',
    'category': 'sale',
    'depends': ['sale', 'account_balance_doc_rep_it'],
    "data": [
        "security/ir.model.access.csv",
        "views/template_sale_finance_views.xml",        
        "wizard/template_sale_finance_wizard.xml"
    ],
    'application': True,
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
