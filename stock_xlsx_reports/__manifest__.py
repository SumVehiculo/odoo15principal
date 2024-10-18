# -*- encoding-*- 
{
    'name': 'Reportes xlsx-Inventario',
    'version': '1.0',
    'description': 'Reporte de Analisis',
    'author': 'ITGRUPO, Jhorel Revilla',
    'license': 'LGPL-3',
    'depends': [
        'stock',
        'account_base_it'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/stock_picking_menu.xml',
        'wizards/stock_analysis_report.xml'
    ],
    'auto_install': False,
    'application': False
}