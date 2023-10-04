# -*- coding: utf-8 -*-
{
    'name' : 'Permiso Creacion Productos',
    'version': '1.0',
    'author': 'ITGRUPO',
    'website': '',
    'category': 'stock',
    'description':
        """
        Permiso Creacion Productos
        """,
    'depends' : ['stock','base','product','purchase'],
    #,'fxo_sale_order_approve'
    'data': [
        'security/group.xml',
        'security/ir.model.access.csv'
    ],
    'auto_install': False,
    'installable': True
}