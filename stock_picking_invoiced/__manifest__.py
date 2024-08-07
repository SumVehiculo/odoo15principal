# -*- coding: utf-8 -*-
{
    'name': "Agregar factura en vista tree",
    'author': 'ITGRUPO, Alessandro Pelayo Mollocondo Medrano',
    'category': 'Stock',
    'description': """Modulo que agrega el campo de factura en la vista tree, este modulo puede ser utilizado para agregar los diferentes campos en la vista tree""",
    'version': '1.0',
    'summary': 'Modificaciones personalizadas para stock',
    'depends': ['stock', 'prorratear_en', 'kardex_fisico_it'],
    'data': [
        'views/views.xml',
    ],
    'demo': [],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}