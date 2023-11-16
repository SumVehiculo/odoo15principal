# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class CrmTeam(models.Model):
    _inherit = 'crm.team'
	
    def _compute_invoiced(self):
        if not self:
            return

        query = '''
            SELECT
                move.team_id AS team_id,
                SUM(move.amount_untaxed_signed) AS amount_untaxed_signed
            FROM account_move move
            WHERE move.move_type IN ('out_invoice', 'out_refund', 'out_receipt')
           
            AND move.state = 'posted'
            AND move.team_id IN %s
            AND move.date BETWEEN %s AND %s
            GROUP BY move.team_id
        '''
        today = fields.Date.today()
        params = [tuple(self.ids), fields.Date.to_string(today.replace(day=1)), fields.Date.to_string(today)]
        self._cr.execute(query, params)

        data_map = dict((v[0], v[1]) for v in self._cr.fetchall())
        for team in self:
            team.invoiced = data_map.get(team.id, 0.0)
