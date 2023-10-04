# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import formatLang, format_date, get_lang


class AccountMove(models.Model):
	_inherit = 'account.move'

	currency_rate = fields.Float(string='Tipo de Cambio',digits=(16,4),default=1)
	glosa = fields.Char(string='Glosa')
	is_opening_close = fields.Boolean(string=u'Apertura/Cierre',default=False)
	perception_date = fields.Date(string='Fecha Uso Percepcion')
	es_editable = fields.Boolean('Es editable',related='journal_id.voucher_edit')
	td_payment_id = fields.Many2one('einvoice.catalog.payment',string='Medio de Pago', copy=False)
	ple_state = fields.Selection([('1','Fecha del Comprobante Corresponde al Periodo'),
								('8','Corresponde a un Periodo Anterior y no ha sido Anotado en dicho Periodo'),
								('9','Corresponde a un Periodo Anterior y si ha sido Anotado en dicho Periodo')],string='Estado PLE Diario', default='1', copy=False)
	date_corre_ple = fields.Date(string='Fecha Ajuste', copy=False)
	c_sire = fields.Boolean(string=u'Complementa SIRE',copy=False,default=False)
	adj_sire = fields.Boolean(string=u'Ajuste SIRE',copy=False,default=False)
	corre_sire = fields.Selection([('0','Adicionar'),('1','Excluir'),('2','Incluir'),('3','Ajuste')],string='Tipo SIRE Compras', copy=False)
	is_descount = fields.Boolean(string=u'Es descuento', default=False)
	serie_id = fields.Many2one('it.invoice.serie',string='Serie')
	acc_number_partner_id = fields.Many2one('res.partner.bank',string=u'Cuenta Bancaria Partner',domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")

	#OBTENER POR DEFAULT LA CTA BANCARIA DEL PARTNER (ES PARTE DEL CAMPO)

	@api.onchange('partner_id')
	def _default_acc_number_partner_id(self):
		self.acc_number_partner_id = self.partner_id.bank_ids and self.partner_id.bank_ids[0]
	
	#Pestaña: SUNAT
	linked_to_detractions = fields.Boolean(string='Sujeto a Detracciones',default=False, copy=False)
	type_op_det = fields.Char(string=u'Tipo de Operación',size=2, copy=False, default='01')
	date_detraccion = fields.Date(string=u'Fecha Detracción', copy=False)
	
	detraction_percent_id = fields.Many2one('detractions.catalog.percent',string='Bien o Servicio', copy=False)
	percentage = fields.Float(related='detraction_percent_id.percentage',readonly=True, copy=False)

	voucher_number = fields.Char(string='Numero de Comprobante', copy=False)
	detra_amount = fields.Float(string='Monto',digits=(16, 2), copy=False)

	linked_to_perception = fields.Boolean(string='Sujeto a Percepcion',default=False, copy=False)
	type_t_perception = fields.Char(string='Tipo Tasa Percepcion',size=3, copy=False)
	number_perception = fields.Char(string='Numero Percepcion',size=6, copy=False)
	automatic_destiny = fields.Boolean(string='Destino automatico',default=False, copy=False)

	register_sunat = fields.Selection(string='Registro SUNAT',related='journal_id.register_sunat',readonly=True)
	journal_type_it = fields.Selection(related='journal_id.type',readonly=True)
	doc_origin_customer = fields.Char(string='Doc Origen Cliente', copy=False)
	doc_invoice_relac = fields.One2many('doc.invoice.relac','move_id')

	#SALES
	campo_09_sale = fields.Char(string='Ultimo Número Consolidado',size=20)
	campo_31_sale = fields.Char(string='Numero de Contrato',size=12)
	campo_32_sale = fields.Boolean(string='Inconsistencia en Tipo de Cambio', default=False)
	campo_33_sale = fields.Boolean(string='Cancelado con Medio de Pago', default=False)
	campo_34_sale = fields.Selection([
									('0',u'Anotacion optativa sin efecto en el IGV'),
									('1',u'Fecha del comprobante corresponde al periodo'),
									('2',u'Documento anulado'),
									('8',u'Corresponde a un periodo anterior'),
									('9',u'Se esta corrigiendo una notacion del periodo anterior')
									],string='Estado PLE Venta',default='1')
	date_modify_sale = fields.Date(string='Fecha Ajuste Venta')

	#PURCHASES
	campo_09_purchase = fields.Char(string='Numero Inicial Consolidado',size=20)
	campo_33_purchase = fields.Boolean(string='Sujeto a Retencion', default=False)
	campo_34_purchase = fields.Selection([
									('1',u'Mercaderia, materia prima, suministro, envases y embalajes'),
									('2',u'Activo Fijo'),
									('3',u'Otros activos no considerados en los numerales 1 y 2'),
									('4',u'Gastos de educacion, recreacion, salud, culturales, representacion, capacitacion, de viaje, mantenimiento de vehiculos, y de premios'),
									('5',u'Otros gastos no incluidos en el numeral 4')
									],string='Tipo de Adquisicion', help='Tabla 30 SUNAT',default='1')
	campo_35_purchase = fields.Char(string='Contrato o Proyecto',size=20)
	campo_36_purchase = fields.Boolean(string='Inconsistencia en Tipo de Cambio', default=False)
	campo_37_purchase = fields.Boolean(string='Proveedor No Habido', default=False)
	campo_38_purchase = fields.Boolean(string='Renuncio Exoineracion al IGV', default=False)
	campo_39_purchase = fields.Boolean(string='Inconsistencia DNI, Liquidacion de Compra', default=False)
	campo_40_purchase = fields.Boolean(string='Cancelado con Medio de Pago', default=False)
	campo_41_purchase = fields.Selection([
									('0',u'ANOTACION OPTATIVAS SIN EFECTO EN EL IGV'),
									('1',u'FECHA DEL DOCUMENTO CORRESPONDE AL PERIODO EN QUE SE ANOTÓ'),
									('6',u'FECHA DE EMISION ES ANTERIOR AL PERIODO DE ANOTACION, DENTRO DE LOS 12 MESES'),
									('7',u'FECHA DE EMISION ES ANTERIOR AL PERIODO DE ANOTACION, LUEGO DE LOS 12 MESES'),
									('9',u'ES AJUSTE O RECTIFICACION')
									],string='Estado PLE Compra',default='1')
	date_modify_purchase = fields.Date(string='Fecha Ajuste Compra')
	participation_percent_sire = fields.Float(string=u'% Participación del Contrato de las Sociedades',copy=False)
	tax_mat_exo_igv_sire = fields.Float(string=u'Impuesto materia de beneficio Ley 31053 - Están exonerados del IGV la importación y/o venta en el país de los libros y productos editoriales afines',copy=False)

	#PLE NO DOMICILIADOS
	campo_26_purchase_nd = fields.Float(string='Renta Bruta',digits=(12, 2)) # It can't be negative
	campo_27_purchase_nd = fields.Float(string='Deduccion Costo Eneajenación',digits=(12, 2))
	campo_28_purchase_nd = fields.Float(string='Renta Neta',digits=(12, 2)) # It can't be negative
	campo_29_purchase_nd = fields.Float(string='Tasa de Retencion',digits=(3, 2)) # It can't be negative
	campo_30_purchase_nd = fields.Float(string='Impuesto Retenido',digits=(12, 2)) # It can't be negative
	campo_32_purchase_nd = fields.Char(help='Tabla 33 SUNAT',string='Exoneracion Aplicada')
	campo_33_purchase_nd = fields.Char(help='Tabla 31 SUNAT',string='Tipo de Renta')
	campo_34_purchase_nd = fields.Char(help='Tabla 32 SUNAT',string='Modalidad de Servicio')
	campo_35_purchase_nd = fields.Boolean(string='Articulo 76 IR', default=False)
	campo_23_purchase_nd = fields.Many2one('res.partner', string='Beneficiario de los Pagos')


	#SUSTENTO CREDITO FISCAL
	campo_11_purchase_nd = fields.Many2one('l10n_latam.document.type',string='Tipo Documento')
	campo_12_purchase_nd = fields.Char(string='Serie',size=20)
	campo_13_purchase_nd = fields.Char(string='Año Emsion DUA',size=4)
	campo_14_purchase_nd = fields.Char(string='Nro Comprobante',size=20)
	campo_15_purchase_nd = fields.Float(string='Monto de Retencion del IGV',digits=(12,2),default=0)

	#OBTENER POR DEFAULT BOOLEAN TC PERSONALIZADO SEGUN TIPO DE ASIENTO (ES PARTE DEL CAMPO)
	@api.model
	def _get_default_tc_per(self):
		move_type = self._context.get('default_move_type', 'entry')
		boole = False
		if move_type in self.get_sale_types(include_receipts=True):
			boole = True
		elif move_type in self.get_purchase_types(include_receipts=True):
			boole = True
		return boole

	tc_per = fields.Boolean(string='Usar Tc Personalizado',copy=False,default=_get_default_tc_per)
	partner_vat = fields.Char(related='partner_id.vat',string='RUC')

	@api.returns('self', lambda value: value.id)
	def copy(self, default=None):
		copied_am = super().copy(default)
		copied_am.l10n_latam_document_type_id = None
		copied_am.line_ids.type_document_id = None
		copied_am.line_ids.nro_comp = None
		return copied_am

class AccountMoveLine(models.Model):
	_inherit = 'account.move.line'

	type_document_id = fields.Many2one('l10n_latam.document.type',string='T.D.',copy=False)
	nro_comp = fields.Char(string='Nro Comp.',size=40,copy=False)
	tc = fields.Float(string='T.C.',digits=(12,4),default=1)
	tax_amount_it = fields.Monetary(default=0.0, currency_field='company_currency_id',string='Importe Imp.',copy=False)
	tax_amount_me = fields.Monetary(default=0.0,string='Importe Imp. ME',copy=False)
	cuo = fields.Integer(string="CUO",copy=False)
	cash_flow_id = fields.Many2one('account.cash.flow',string="Flujo Caja")
	invoice_date_it = fields.Date(string=u'Fecha Emisión')
	is_p = fields.Boolean(string=u'Es Provisión',default=False)
	cta_cte_origen = fields.Boolean(string=u'Es cta cte Origen',default=False)