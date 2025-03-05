# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class AccountBankStatement(models.Model):
    _inherit = 'account.bank.statement'

    def action_draft_force(self):
        for i in self:
            sql = """update account_bank_statement set state = 'open' where id = %s""" % (i.id)
            i.env.cr.execute(sql)
        return {
        'type': 'ir.actions.client',
        'tag': 'reload',
        }