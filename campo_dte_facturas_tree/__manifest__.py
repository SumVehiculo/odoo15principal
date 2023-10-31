# -*- encoding:utf-8 -*-
{
    'name': 'Campo "Estado de DTE en SUNAT" en facturas tree',
    'version': '1.0',
    'description': 'Agrega el campo "Estado de DTE en SUNAT" a la vista tree en facturas.',
    'author': 'ITGRUPO, Jhorel Revilla Calderon',
    'license': 'LGPL-3',
    'depends': [
        'account',
        'account_edi'
    ],
    'data': [
        'views/inherit.xml'
    ],
    'auto_install': False,
    'application': False
}