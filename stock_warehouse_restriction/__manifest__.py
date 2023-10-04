# -*- coding: utf-8 -*-
{
    'name' : 'Permiso Creacion Almacen Ubicacion y Tipo Operacion',
    'version': '1.0',
    'author': 'ITGRUPO',
    'website': '',
    'category': 'stock',
    'description':
        """
        Permiso Creacion Almacen Ubicacion y Tipo Operacion
        """,
    'depends' : ['stock','base'],
    #,'fxo_sale_order_approve'
    'data': [
        'security/group.xml'
    ],
    'auto_install': False,
    'installable': True
}