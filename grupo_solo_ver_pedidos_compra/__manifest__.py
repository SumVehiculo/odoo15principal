# -*- encoding:ut-8 -*-
{
    'name': 'Grupo-Pedidos de Compra: Crear, Editar y Borrar',
    'version': '1.0',
    'description': 'Modulo que agrega un grupo solo ver la SDP y PDC.',
    'author': 'ITGRUPO, Jhorel Revilla Calderon',
    'license': 'LGPL-3',
    'depends': [
        'purchase'
    ],
    'data': [
        'security/grupo.xml',
        'views/inherit_raro.xml'
    ],
    'auto_install': False,
    'application': False,
}