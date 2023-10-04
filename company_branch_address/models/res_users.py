# -*- coding: utf-8 -*-
from odoo import api, fields, models
import logging
_logger = logging.getLogger(__name__)

class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model
    def operating_unit_default_get(self, uid2):
        if not uid2:
            uid2 = self._uid
        user = self.env['res.users'].browse(uid2)
        return user.default_company_branch_address_id

    @api.model
    def _get_operating_unit(self):
        return self.operating_unit_default_get(self._uid)

    @api.model
    def _get_operating_units(self):
        return self._get_operating_unit()

    company_branch_address_ids = fields.Many2many('res.company.branch.address',
                                          'res_company_branch_address_users_rel',
                                          'user_id', 'rcb_id', 'Establecimientos anexos',
                                          default=_get_operating_units)
    default_company_branch_address_id = fields.Many2one('res.company.branch.address',
                                                'Establecimiento anexo por defecto',
                                                default=_get_operating_unit)
