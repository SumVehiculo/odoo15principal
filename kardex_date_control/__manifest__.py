# -*- coding: utf-8 -*-
{
    'name': "Control fecha kardex",
    'author': 'ITGRUPO, Alessandro Pelayo Mollocondo Medrano',
    'category': 'Inventory',
    'description': """Controla con un raise para que no se pueda agregar la fecha kardex en los albarnes si estos se enceuntran en estado borrador para que no haya un problema de quien lo modifico, ya que este campo si llega a aparecer en el social una vez que el objeto stock.picking este creado""",
    'version': '1.0',
    'summary': 'Modificaciones personalizadas para stock',
    'depends': ['kardex_fisico_it'],
    'data': [
    ],
    'demo': [],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}