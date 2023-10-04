# -*- coding: utf-8 -*-
from odoo import api, fields, models
import logging
log = logging.getLogger(__name__)

class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = 'sale.advance.payment.inv'

    def create_invoices(self):
        Sale = self.env['sale.order'].browse(self._context.get('active_id', False))
        before_invoices = Sale.invoice_ids

        res = super(SaleAdvancePaymentInv, self).create_invoices()

        after_invoices = Sale.invoice_ids
        new_invoice = after_invoices - before_invoices

        picking_hook = self.env['ir.module.module'].search([('name', '=', 'stock_move_picking_hook')])
        if picking_hook and picking_hook.state == 'installed':
            for picking in self.picking_ids:
                if picking.despatch_id:
                    if picking.despatch_id.name:
                        sequence_split = picking.despatch_id.name.split('-')
                        if len(sequence_split)==2:
                            self.env['account.move.transportref'].create({
                                    'move_id': new_invoice.id,
                                    'ref_type':'09',
                                    'ref_serial': sequence_split[0],
                                    'ref_number': sequence_split[1]
                                })
        return res