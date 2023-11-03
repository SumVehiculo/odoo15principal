# -*- enconding:utf-8 -*-
{
    'name': 'Agregar nro comprobante a plantilla de Facturas',
    'version': '1.0',
    'description': 'Modulo que modifica campos de la plantilla de Facturas.',
    'author': 'ITGRUPO, Jhorel Revilla Calderon',
    'license': 'LGPL-3',
    'depends': [
        'l10n_pe_edi_extended'
    ],
    'data': [
        'views/inherit_mail.xml'
    ],
    'auto_install': False,
    'application': False
}