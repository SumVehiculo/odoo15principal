# -*- coding: utf-8 -*-
{
    'name' : 'Esconder Transferencias Inmediatas',
    'version': '1.0',
    'author': 'ITGRUPO',
    'website': '',
    'category': 'stock',
    'description':
        """
        Esconder Transferencias Inmediatas
        """,
    'depends' : ['stock','base'],
    #,'fxo_sale_order_approve'
    'data': [
        'views/stock_picking_no_inmediate_transfer.xml'
    ],
    'auto_install': False,
    'installable': True
}