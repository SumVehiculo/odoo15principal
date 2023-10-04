# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ResCompany(models.Model):
    _inherit = "res.company"

    def _localization_use_documents(self):
        """ Peruvian localization use documents """
        self.ensure_one()
        return self.country_id.code == "PE" or super()._localization_use_documents()
