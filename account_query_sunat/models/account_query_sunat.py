# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
import base64
from io import BytesIO
import uuid

class AccountQuerySunat(models.Model):
	_name = 'account.query.sunat'

	move_id = fields.Many2one('account.move',string='Factura')
	
	name = fields.Char(default=u'...')
	success = fields.Boolean(string='Estado Consulta')
	message = fields.Char(string=u'Mensaje del estado de la operación')
	estadocp = fields.Selection([('0','NO EXISTE'),
								('1','ACEPTADO'),
								('2',u'ANULADO'),
								('3','AUTORIZADO'),
								('4','NO AUTORIZADO')],string=u'Estado del Comprobante')
	estadoruc = fields.Selection([('00','ACTIVO'),
								('01','BAJA PROVISIONAL'),
								('02',u'BAJA PROV. POR OFICIO'),
								('03','SUSPENSION TEMPORAL'),
								('10','BAJA DEFINITIVA'),
								('11','BAJA DE OFICIO'),
								('22','INHABILITADO-VENT.UNICA')],string=u'Estado del Contribuyente')
	conddomiruc = fields.Selection([('00','HABIDO'),
								('09','PENDIENTE'),
								('11',u'POR VERIFICAR'),
								('12','NO HABIDO'),
								('20','NO HALLADO')],string=u'Condición de Domicilio del Contribuyente')
	observaciones = fields.Char(string=u'Observaciones')			
	errorcode = fields.Char(string=u'Código de Error')		
	company_id = fields.Many2one(related='move_id.company_id', store=True, readonly=True)

	td_p_id = fields.Many2one(
		'l10n_latam.document.type',
		string='TD',
		related='move_id.l10n_latam_document_type_id'
		)
	nro_comprobante = fields.Char(
		string="NRO COMPROBANTE",
		related='move_id.ref',
		)
	proveedor_id = fields.Many2one(
		'res.partner',
		string = 'PROVEEDOR',
		related='move_id.partner_id'
		)
	doc_proveedor = fields.Char(
		string = "DOC PROVEEDOR",
		related='proveedor_id.vat'
	)