# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class KardexEntryOutcomeBook(models.Model):
    _inherit = 'kardex.entry.outcome.book'


    work_order_id = fields.Many2one('project.project', string='Orden de Trabajo')