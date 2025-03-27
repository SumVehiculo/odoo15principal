# -*- encoding: utf-8 -*-
{
    'name': 'Campo Clasificacion en PRODUCTOS',
    'version': '1.0',
    'description': 'Campo Clasificacion en PRODUCTOS',
    'author': 'ITGRUPO, Jhorel Revilla',
    'license': 'LGPL-3',
    'depends': [
        'kardex_formato_sunat_it'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/product_classification.xml',
        'views/product_template.xml',
    ],
    'auto_install': False,
    'application': False,
}