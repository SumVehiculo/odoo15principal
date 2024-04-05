# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ResBank(models.Model):
    _inherit = 'res.bank'

    format_bank = fields.Selection([
    	('bbva', 'Formato BBVA'),
    	('bcp', 'Formato BCP'),
    	('interbank', 'Formato Interbank'),
    	('scotiabank', 'Formato Scotiabank'),
        ('banbif', 'Formato BanBif'),
    	], string='Formato de Txt')

    # bb_bankcode=fields.Selection([
    #     ('001','BANCO CENTRAL DE RESERVA'),
    #     ('002','BANCO DE CREDITO'),
    #     ('003','BANCO INTERBANK'),
    #     ('007','CITIBANK'),
    #     ('009','BANCO SCOTIABANK'),
    #     ('011','BANCO CONTINENTAL'),
    #     ('018','BANCO NACION'),
    #     ('023','BANCO DE COMERCIO'),
    #     ('035','BANCO FINANCIERO'),
    #     ('038','BANBIF'),
    #     ('043','CREDISCOTIA FINANCIERA S.'),
    #     ('049','MI BANCO'),
    #     ('053','BANCO GNB'),
    #     ('054','BANCO FALABELLA'),
    #     ('056','BANCO SANTANDER PERU SAC'),
    #     ('800','CAJA METROPOLITANA DE LIM'),
    #     ('801','CMAC PIURA'),
    #     ('803','CMAC AREQUIPA'),
    #     ('805','CMAC SULLANA'),
    #     ('806','CMAC CUZCO'),
    #     ('808','CMAC HUANCAYO'),
    #     ],  string='Codigo Banco')