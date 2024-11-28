# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class TemplateSaleFinance(models.Model):
    _name = 'template.sale.finance'
    _description = 'TemplateSaleFinance'
    _auto =  False
    
    account = fields.Char(string=_('Cuenta'))
    debit = fields.Float(string=_('Debito'))
    credit = fields.Float(string=_('Credito'))
    currency = fields.Char(string=_('Moneda'))
    amount_currency = fields.Float(string=_('Importe Moneda'))
    tc = fields.Float(string=_('TC'))
    partner = fields.Char(string=_('Cliente'))
    td = fields.Char(string=_('TD'))
    nro_comp = fields.Char(string=_('Nro Comp'))
    date = fields.Date(string=_('Fecha Doc'))
    sale_date = fields.Date(string=_('Fecha del Pedido'))
    cta_analytic = fields.Char(string=_('Cuenta Analitica'))
    analytic_tags = fields.Char(string=_('Etiquetas Analiticas'))