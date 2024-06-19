# -*- coding: utf-8 -*-
{
    'name': "Actualiza Factura Albaràn",
    'author': 'ITGRUPO, Alessandro Pelayo Mollocondo Medrano',
    'category': 'Stock',
    'description': """Modulo que permite actualizar la factura en los albaranes""",
    'version': '1.0',
    'summary': 'Modificaciones personalizadas para stock',
    'depends': ['kardex_fisico_it'],
    'data': [
        'security/ir.model.access.csv',
        'views/wizard.xml',
    ],
    'demo': [],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}