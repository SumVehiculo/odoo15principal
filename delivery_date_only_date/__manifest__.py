# -*- enconding:utf-8 -*-
{
    'name': 'Delivery Date only Date',
    'version': '1.0',
    'description': 'Modulo que agrega el widget date a los campos de fecha de entrega en VENTAS/COMPRAS. ',
    'author': 'ITGRUPO, Jhorel Revilla',
    'license': 'LGPL-3',
    'depends': [
        'purchase',
        'sale_stock'
    ],
    'data': [
        'views/purchase.xml',
        'views/sale_stock.xml'
    ],
    'auto_install': False,
    'application': False,
}