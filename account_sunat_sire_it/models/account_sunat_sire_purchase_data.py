# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
import base64
from io import BytesIO
import uuid

class AccountSunatSirePurchaseData(models.Model):
	_name = 'account.sunat.sire.purchase.data'
	
	perPeriodoTributario = fields.Char(string=u'Periodo Tributario')
	codCar = fields.Char(string=u'CAR Sunat')
	fecEmision = fields.Date(string=u'Fecha de Emisión')
	fecVencPag = fields.Date(string=u'Fecha Vencimiento')
	codTipoCDP = fields.Char(string=u'Tipo de Comprob.')
	numSerieCDP = fields.Char(string=u'Serie')
	anio = fields.Char(string=u'Año')
	numCDP = fields.Char(string=u'Número')
	nro_final = fields.Char(string=u'Número Final')
	codTipoDocIdentidad = fields.Char(string=u'Tipo Documento Identidad')
	numDocIdentidad = fields.Char(string=u'Número de Documento')
	nomRazonSocialCliente = fields.Char(string=u'Denominación o Razon Social')

	mto_bi_dg = fields.Float(string=u'BI Gravado DG')
	igv_dg = fields.Float(string=u'IGV / IPM DG')
	mto_bi_dgng = fields.Float(string=u'BI Gravado DGNG')
	igv_dgng = fields.Float(string=u'IGV / IPM DGNG')
	mto_bi_dng = fields.Float(string=u'BI Gravado DNG')
	igv_dng = fields.Float(string=u'IGV / IPM DNG')

	valor_adq_ng = fields.Float(string=u'Valor Adq. NG')
	mtoISC = fields.Float(string=u'ISC')
	mtoIcbp = fields.Float(string=u'ICBPER')
	mtoOtrosTrib = fields.Float(string=u'Otros Conceptos, Tributos Y Cargos que no forman parte de la Base Imponible')
	mtoTotalCP = fields.Float(string=u'Importe Total del Comprobante de Pago')

	codMoneda = fields.Char(string=u'Código de la Moneda')
	mtoTipoCambio = fields.Float(string=u'Tipo de Cambio')
	
	fecEmisionMod = fields.Date(string=u'Fecha Documento que se Modifica')
	codTipoCDPMod = fields.Char(string=u'Tipo Comprob. Documento que se Modifica')
	numSerieCDPMod = fields.Char(string=u'Serie Documento que se Modifica')
	cod_dam = fields.Char(string=u'COD DAM')
	numCDPMod = fields.Char(string=u'Número Documento que se Modifica')
	bi_o_ser = fields.Char(string=u'Clasif de Bss y Sss')
	id_proyecto_op = fields.Char(string=u'ID Proyecto Operadores')
	por_part = fields.Float(string=u'PorcPart')
	imb = fields.Char(string=u'IMB')
	car_orig = fields.Char(string=u'CAR Orig/ Ind E o I')
	detraccion = fields.Float(string=u'Detracción')
	tipo_nota = fields.Char(string=u'Tipo de Nota')
	estado_comp = fields.Char(string=u'Est. Comp.')
	incal = fields.Char(string=u'Incal')