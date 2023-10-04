{
    'name': 'Albaran agregar botón mrp',
    'version': '1.0',
    'description': 'Albaran agregar botón mrp',
    'author': 'ITGRUPO',
    'license': 'LGPL-3',
    'category': 'Sumtec',
    'auto_install': False,
    'depends': [
    #     'sale',
    #     'project',
    #     'account'
        'stock_balance_report','stock_balance_report_lote','mrp','stock','albaranbutton'
    ],
    'data': [
        'views/ir.model.access.csv',
        'views/button.xml',
    ],
    'installable': True
}