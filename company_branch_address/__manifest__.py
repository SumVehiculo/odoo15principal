# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011 Cubic ERP - Teradata SAC (<http://cubicerp.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    "name": "Company Branch Address",
    "description": "Agrega gestion de establecimientos anexos a la empresa matriz",
    "depends": ["base"],
    "data": [
    	'security/res_company_branch_address_security.xml',
        "security/ir.model.access.csv",
    	#'security/ir.model.access.csv',
        'views/company_branch_address_view.xml',
        'views/res_users_view.xml',
        #'views/template.xml'
        ],
    'qweb': [],
    'application': False,
}
