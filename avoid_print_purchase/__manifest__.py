#-*- encoding: utf-8 -*-
{
    'name': 'Evitar imprimir OD cuando no esta confirmada',
    'version': '1.0',
    'description': 'Solo muestra la Orden de Compra cuando esta en estado Orden de Compra',
    'author': 'ITGRUPO, Jhorel Revilla',
    'license': 'LGPL-3',
    'depends': [
        'purchase'
    ],
    'data': [
        'report/report_purchaseorder.xml'
    ],
    'auto_install': False,
    'application': False
}