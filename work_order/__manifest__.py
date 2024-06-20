# -*- encoding:utf-8 -*-
{
    'name': 'Orden de Trabajo',
    'version': '1.0',
    'description': 'Crea el correlativo y las relaciones necesarias en las lineas de compra, albaranes y factura',
    'author': 'ITGRUPO, Jhorel Revilla',
    'license': 'LGPL-3',
    'depends': [
        'project',
        'purchase',
        'stock',
        'stock_move_picking_hook'
    ],
    'data': [
        'views/project_project.xml',
        'views/purchase_order.xml',
        'views/stock_picking.xml',
        'views/account_move.xml',
        'views/sale_order.xml',
    ],
    'auto_install': False,
    'application': False
}