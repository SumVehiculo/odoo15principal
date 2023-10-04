# -*- coding: utf-8 -*-
{
    'name': "Agregar dominios",
    'author': 'ITGRUPO, berth',
    'category': 'Sale, Purchase',
    'description': """Agregar dominios a campos de sale y purchase""",
    'version': '1.0',
    'depends': ['sale','purchase','account_fields_it'],
    'data': [
        'views/purchase_dominio.xml',
        'views/sale_dominio.xml',
    ],
    'demo': [],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}