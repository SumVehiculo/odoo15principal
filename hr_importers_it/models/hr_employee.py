# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import format_time

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    # work_contact_id = fields.Many2one('res.partner', 'Work Contact', copy=False)
    identification_id = fields.Char(store=True, inverse='_inverse_create_partner')

    def _inverse_create_partner(self):
        for employee in self:
            partner = self.env['res.partner'].search([('vat', '=', employee.identification_id)], limit=1)
            if not partner:
                partner = self.env['res.partner'].sudo().create({
                    'is_company': False,
                    'type': 'contact',
                    'name': employee.name,
                    'name_p': employee.names,
                    'last_name': employee.last_name,
                    'm_last_name': employee.m_last_name,
                    'street': employee.address,
                    'email':employee.work_email,
                    'phone': employee.work_phone,
                    'mobile': employee.mobile_phone,
                    'l10n_latam_identification_type_id': self.env['l10n_latam.identification.type'].search(
                        [('name', '=', employee.type_document_id.name)], limit=1).id,
                    'vat': employee.identification_id,
                    'ref': employee.identification_id,
                    'employee': True,
                    'is_employee': True,
                    'image_1920': employee.image_1920,
                    # 'company_id': employee.company_id.id
                })
            if not employee.address_home_id:
                employee.address_home_id = partner.id