# -*- encoding:ut-8 -*-
{
    'name': 'Grupo-Albaranes: Crear, Editar y Borrar',
    'version': '1.0',
    'description': 'Modulo que agrega un grupo para solo ver transferencias.',
    'author': 'ITGRUPO, Jhorel Revilla Calderon',
    'license': 'LGPL-3',
    'depends': [
        'stock',
        'prorratear_en',
        'kardex_fisico_it'
    ],
    'data': [
        'security/grupo.xml',
        'views/inherit_raro.xml'
    ],
    'auto_install': False,
    'application': False,
}