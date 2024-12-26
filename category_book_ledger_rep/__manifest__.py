# -*- coding: utf-8 -*-
{
    'name': 'Categoria para el Libro Mayor',
    'summary': """ Nueva agrupacion Libro Mayor (#33209 """,
    'author': 'ITGRUPO, Sebastian Moises Loraico Lopez',
    'category': 'account',
    'depends': ['account_fields_it', ],
    "data": [
        "views/account_move_line_views.xml"
    ],
    'application': True,
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
