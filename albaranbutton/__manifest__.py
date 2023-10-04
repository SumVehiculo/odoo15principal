{
    'name': 'Albaran agregar botón',
    'version': '1.0',
    'description': 'Boton para albanares',
    'author': 'ITGRUPO',
    'license': 'LGPL-3',
    'category': 'Sumtec',
    'auto_install': False,
    'depends': [
    #     'sale',
    #     'project',
    #     'account'
        'stock_balance_report','stock_balance_report_lote'
    ],
    'data': [
        # 'security/ir.model.access.csv',
        'views/button.xml',
    ],
    'installable': True
}