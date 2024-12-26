# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    category_ids = fields.Many2many(
        string=_('Categorías'),
        relation='move_line_category_partner',
        related='partner_id.category_id',
        column1='aml_id',
        column2='category_id',
        store = True
    )