# -*- encoding:utf-8 -*-
{
    'name': 'Aprobacion de Compras',
    'version': '1.0',
    'description': 'Agrega descripcion de la persona que aprobo y la fecha correcta segun la aprobacion nativa de odoo',
    'summary': '',
    'author': 'ITGRUPO, Jhorel Revilla',
    'license': 'LGPL-3',
    'depends': [
        'purchase'
    ],
    'data': [
        'security/res_groups.xml',
        'views/purchase_order.xml'
    ],
    'auto_install': False,
    'application': False
}