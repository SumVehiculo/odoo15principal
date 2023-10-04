# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
import base64
from io import BytesIO
import uuid

class AccountSunatSireSaleData(models.Model):
	_name = 'account.sunat.sire.sale.data'

	move_id = fields.Many2one('account.move',string='Factura')
	
	sire_id = fields.Char(string=u'ID Sire')
	perPeriodoTributario = fields.Char(string=u'Periodo Tributario')
	codCar = fields.Char(string=u'CAR Sunat')
	codTipoCDP = fields.Char(string=u'Tipo de Comprob.')
	numSerieCDP = fields.Char(string=u'Serie')
	numCDP = fields.Char(string=u'Número')
	codTipoCarga = fields.Char(string=u'Código de Tipo de Carga')
	codSituacion = fields.Char(string=u'Código Situación')
	fecEmision = fields.Date(string=u'Fecha de Emisión')
	fecVencPag = fields.Date(string=u'Fecha Vencimiento')
	codTipoDocIdentidad = fields.Char(string=u'Tipo Documento Identidad')
	numDocIdentidad = fields.Char(string=u'Número de Documento')
	nomRazonSocialCliente = fields.Char(string=u'Denominación o Razon Social')
	mtoValFactExpo = fields.Float(string=u'Valor Facturado de la Exportación')
	mtoBIGravada = fields.Float(string=u'Base Imponible de la Operación Gravada')
	mtoDsctoBI = fields.Float(string=u'Descuento de la Base Imponible')
	mtoIGV = fields.Float(string=u'IGV Y/O IPM')
	mtoDsctoIGV = fields.Float(string=u'Descuento de IGV Y/O IPM')
	mtoExonerado = fields.Float(string=u'Importe Total de la Operación Exonerada')
	mtoInafecto = fields.Float(string=u'Importe Total de la Operación Inafecta')
	mtoISC = fields.Float(string=u'ISC')
	mtoBIIvap = fields.Float(string=u'Base Imponible de la Operación Gravada con el IVAP')
	mtoIvap = fields.Float(string=u'Impuesto de la Venta del Arroz Pilado (IVAP)')
	mtoIcbp = fields.Float(string=u'ICBPER')
	mtoOtrosTrib = fields.Float(string=u'Otros Conceptos, Tributos Y Cargos que no forman parte de la Base Imponible')
	mtoTotalCP = fields.Float(string=u'Importe Total del Comprobante de Pago')
	codMoneda = fields.Char(string=u'Código de la Moneda')
	mtoTipoCambio = fields.Float(string=u'Tipo de Cambio')
	codEstadoComprobante = fields.Char(string=u'Código Estado Comprobante')
	desEstadoComprobante = fields.Char(string=u'Descripción Estado Comprobante')
	indOperGratuita = fields.Char(string=u'Ind Oper. Gratuita')
	mtoValorOpGratuitas = fields.Float(string=u'Valor Referencial Oper. Gratuita')
	mtoValorFob = fields.Float(string=u'Valor FOB Exportación Embarcado')
	indTipoOperacion = fields.Char(string=u'Tipo de Operación')
	mtoPorcParticipacion = fields.Float(string=u'%% de Participación en el Contrato')
	mtoValorFobDolar = fields.Float(string=u'Valor FOB Dólares')
	fecEmisionMod = fields.Date(string=u'Fecha Documento que se Modifica')
	codTipoCDPMod = fields.Char(string=u'Tipo Comprob. Documento que se Modifica')
	numSerieCDPMod = fields.Char(string=u'Serie Documento que se Modifica')
	numCDPMod = fields.Char(string=u'Número Documento que se Modifica')