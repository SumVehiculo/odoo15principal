# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
{
    "name" : "Importar Diarios de bancos y caja",
    "author" : "ITGRUPO, Sebastian Moises Loraico Lopez",
    "category": "Purchases",
    "description": """Este modulo es para importar diarios de bancos y cajas""", 
    "version":"15.0.0",
    "depends" : ["popup_it",'account_menu_other_configurations'],
    "application" : True,
    "data" : [
             'data/attachment_sample.xml',
            'security/ir.model.access.csv',
            'wizard/journal_bank_cash_wizard.xml',
            ],
    
    "auto_install":False,
    "installable" : True,   
    "license" : "LGPL-3"
}
