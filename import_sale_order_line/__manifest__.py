# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
{
    "name" : "Importar líneas de pedido de venta desde un archivo CSV/Excel",
    "author" : "Softhealer Technologies-ITGRUPO",
    "website": "https://www.softhealer.com",
    "support": "support@softhealer.com",    
    "category": "Sales",
    "summary": "Importar líneas de orden de venta desde CSV, Importar líneas de orden de venta desde Excel, Importar líneas de RFQ desde el módulo CSV, Importar líneas de RFQ desde la aplicación Excel, Importar líneas de orden de compra desde CSV, importar líneas de orden de compra desde XLS, importar solicitud de línea de cotización XLSX Odoo",
    "description": """Este módulo es útil para importar líneas de órdenes de venta desde CSV/Excel. Puede importar campos personalizados desde CSV o Excel.""", 
    "version":"15.0.0",
    "depends" : ["base", "popup_it", "sale"],
    "application" : True,
    "data" : [
            'data/attachment_sample.xml',
            'security/import_sol_security.xml',
            'security/ir.model.access.csv',
            'wizard/import_sol_wizard.xml',
            'views/sale_view.xml',
            ],
    'external_dependencies' : {
         'python' : ['xlrd'],
    },
    "images": ["static/description/background.png", ],
    "live_test_url": "https://youtu.be/skJ5O8yV3gY",
    "auto_install":False,
    "installable" : True,
    "price": 15,
    "currency": "EUR"   
}
