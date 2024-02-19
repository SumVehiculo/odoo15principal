# -*- coding: utf-8 -*-
{
    'name': "Cuenta analiticas en funcion al tipo de operación",
    'author': 'ITGRUPO, Alessandro Pelayo Mollocondo Medrano',
    'category': 'Stock',
    'description': """Modulo que permite el contorl de las cuentas analiticas si es que estas no estan llenas si en el tipo de operacion no esta activado el campo definido el alabaran podra validar, si en el caso este activado deveria de validar todas las cuentas analiticas y tiene que mostrar advertencias si es que estas estarian vacias""",
    'version': '1.0',
    'summary': 'Modificaciones personalizadas para stock',
    'depends': ['stock'],
    'data': [
        'views/add.xml',
    ],
    'demo': [],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}