from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError
import base64

from io import BytesIO
import re
import uuid
import zipfile
from datetime import datetime, timedelta
import io

import urllib.parse
import requests
import json

BOOK_SIRE = [
	{'name': 'ACEPTA LA PROPUESTA (VENTAS)' ,'nro': 1,'type':'v'},
	{'name': 'REEMPLAZA LA PROPUESTA (VENTAS)' ,'nro': 2,'type':'v'},
	{'name': 'AJUSTES POSTERIORES (VENTAS)' ,'nro': 3,'type':'v'},
	{'name': 'AJUSTES POSTERIORES PLE (VENTAS)' ,'nro': 4,'type':'v'},
	{'name': 'COMPLEMENTAR PROPUESTA (VENTAS)' ,'nro': 5,'type':'v'},
	{'name': 'ACEPTA LA PROPUESTA (COMPRAS)' ,'nro': 1,'type':'c'},
	{'name': u'REEMPLAZA/COMPARA PROPUESTA (COMPRAS)' ,'nro': 2,'type':'c'},
	{'name': 'COMPLEMENTA PROPUESTA (COMPRAS)' ,'nro': 3,'type':'c'},
	{'name': 'AJUSTES POSTERIORES (COMPRAS)' ,'nro': 4,'type':'c'},
	{'name': 'AJUSTES POSTERIORES PLE (COMPRAS)' ,'nro': 5,'type':'c'},
	{'name': 'OPERACIONES NO DOMICILIADOS (COMPRAS)' ,'nro': 6,'type':'c'},
	{'name': 'AJUSTE OPERACIONES NO DOMICILIADOS (COMPRAS)' ,'nro': 7,'type':'c'},
	{'name': 'AJUSTE OPERACIONES NO DOMICILIADOS PLE (COMPRAS)' ,'nro': 8,'type':'c'},
]

class AccountSunatRep(models.TransientModel):
	_inherit = 'account.sunat.wizard'

	type_show =  fields.Selection([('pantalla','Pantalla'),('excel','Excel')],default='pantalla',string=u'Mostrar en', required=True)
	given_numer = fields.Integer(string=u'Número de Entrega')
	document_file = fields.Binary(string='Cargar')
	name_file = fields.Char(string='Nombre de Archivo')
	comp_pr = fields.Boolean(string='Comparar propuesta',default=False)
	compl_type = fields.Selection([('0','Adicionar'),('1','Excluir'),('2','Incluir')],string='Tipo')

	############ Ventas #########
	def get_ventas_sire_1(self):
		self.get_data_from_api_sale()
		if self.type_show == 'pantalla':
			view = self.env.ref('account_sunat_sire_it.account_sunat_sire_sale_data_tree').id
			return {
				'name': 'REGISTRO DE VENTAS - RVIE SUNAT %s %s'%(self.company_id.partner_id.vat,self.period_id.code),
				'type': 'ir.actions.act_window',
				'res_model': 'account.sunat.sire.sale.data',
				'view_mode': 'tree',
				'views': [(view, 'tree')],
			}
		else:
			import io
			from xlsxwriter.workbook import Workbook
			from xlsxwriter.utility import xl_rowcol_to_cell
			ReportBase = self.env['report.base']

			direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

			if not direccion:
				raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

			workbook = Workbook(direccion +'SIREVENTAS.xlsx')
			workbook, formats = ReportBase.get_formats(workbook)

			formats['boldbord'].set_font_size(8)

			import importlib
			import sys
			importlib.reload(sys)

			worksheet = workbook.add_worksheet("REVIE - VENTAS")

			worksheet.merge_range(1,0,1,8, "REGISTRO DE VENTAS - RVIE SUNAT%s %s"%(self.company_id.partner_id.vat,self.period_id.code), formats['especial5'] )

			#CABECERA
			worksheet.merge_range(4,0,6,0,"ESTADO DEL COMPROBANTE", formats['boldbord'] )
			worksheet.merge_range(4,1,6,1,"CAR SUNAT", formats['boldbord'] )
			worksheet.merge_range(4,2,4,8,"INFORMACIÓN RESPECTO AL COMPROBANTE DE PAGO UTILIZADO", formats['boldbord'] )
			worksheet.merge_range(5,2,6,2,"PERIODO TRIBUTARIO", formats['boldbord'] )
			worksheet.merge_range(5,3,6,3,u"FECHA DE EMISIÓN", formats['boldbord'] )
			worksheet.merge_range(5,4,6,4,"FECHA DE VENCIMIENTO O PAGO", formats['boldbord'] )
			worksheet.merge_range(5,5,6,5,"TIPO DE COMPROB.", formats['boldbord'] )
			worksheet.merge_range(5,6,6,6,"SERIE", formats['boldbord'] )
			worksheet.merge_range(5,7,6,7,u"NÚMERO", formats['boldbord'] )
			worksheet.merge_range(5,8,6,8,u"NÚMERO / FINAL", formats['boldbord'] )
			worksheet.merge_range(4,9,4,11,u"INFORMACIÓN DEL PROVEEDOR", formats['boldbord'] )
			worksheet.merge_range(5,9,5,10,u"DOCUMENTO DE IDENTIDAD", formats['boldbord'] )
			worksheet.write(6,9,"TIPO DE DOCUMENTO" ,formats['boldbord'])
			worksheet.write(6,10,u"NÚMERO DE DOCUMENTO" ,formats['boldbord'])
			worksheet.merge_range(5,11,6,11,u"DENOMINACIÓN O RAZÓN SOCIAL / APELLIDOS Y NOMBRES", formats['boldbord'] )
			worksheet.merge_range(4,12,6,12,u"VALOR FACTURADO DE LA EXPORTACIÓN", formats['boldbord'] )
			worksheet.merge_range(4,13,6,13,u"BASE IMPONIBLE DE OPERACIÓN GRAVADA", formats['boldbord'] )
			worksheet.merge_range(4,14,6,14,u"DESCUENTO DE LA BASE IMPONIBLE", formats['boldbord'] )
			worksheet.merge_range(4,15,6,15,u"IGV Y/O IPM", formats['boldbord'] )
			worksheet.merge_range(4,16,6,16,u"DESCUENTO IGV Y/O IPM", formats['boldbord'] )
			worksheet.merge_range(4,17,6,17,u"IMPORTE TOTAL DE LA OPERACIÓN EXONERADA", formats['boldbord'] )
			worksheet.merge_range(4,18,6,18,u"IMPORTE TOTAL DE LA OPERACIÓN INAFECTA", formats['boldbord'] )
			worksheet.merge_range(4,19,6,19,u"ISC", formats['boldbord'] )
			worksheet.merge_range(4,20,6,20,u"BASE IMPONIBLE DE LA OPERACIÓN GRAVADA CON EL IVAP", formats['boldbord'] )
			worksheet.merge_range(4,21,6,21,u"IMPUESTO A LAS VENTAS DEL ARROZ PILADO (IVAP)", formats['boldbord'] )
			worksheet.merge_range(4,22,6,22,u"ICBPER", formats['boldbord'] )
			worksheet.merge_range(4,23,6,23,u"OTROS CONCEPTOS, TRIBUTOS Y CARGOS QUE NO FORMAN PARTE DE LA BASE IMPONIBLE", formats['boldbord'] )
			worksheet.merge_range(4,24,6,24,u"IMPORTE TOTAL DEL COMPROBANTE DE PAGO", formats['boldbord'] )
			worksheet.merge_range(4,25,5,26,u"MONEDA DEL COMPROBANTE", formats['boldbord'] )
			worksheet.write(6,25,u"CÓDIGO DE LA MONEDA" ,formats['boldbord'])
			worksheet.write(6,26,u"TIPO DE CAMBIO" ,formats['boldbord'])
			worksheet.merge_range(4,27,5,30,u"REFERENCIA DEL COMPROBANTE DE PAGO ORIGINAL QUE SE MODIFICA", formats['boldbord'] )
			worksheet.write(6,27,u"FECHA" ,formats['boldbord'])
			worksheet.write(6,28,u"TIPO" ,formats['boldbord'])
			worksheet.write(6,29,u"SERIE" ,formats['boldbord'])
			worksheet.write(6,30,u"NÚMERO" ,formats['boldbord'])
			worksheet.merge_range(4,31,6,31,u"CODIGO TIPO MOTIVO NOTA", formats['boldbord'] )
			worksheet.merge_range(4,32,5,33,u"OPERADORES O PARTÍCIPES DE LAS SOCIEDADES IRREGULARES, CONSORCIOS, JOINT VENTURES U OTRAS FORMAS DE CONTRATOS DE COLABORACIÓN EMPRESARIAL", formats['boldbord'] )
			worksheet.write(6,32,u"ID PROYECTO OPERADORES/ PARTÍCIPES" ,formats['boldbord'])
			worksheet.write(6,33,u"% DE PARTICIPACIÓN EN EL CONTRATO O PROYECTO" ,formats['boldbord'])
			worksheet.merge_range(4,34,6,34,u"VALOR FOB EXPORTACIÓN EMBARCADO", formats['boldbord'] )
			worksheet.merge_range(4,35,6,35,u"VALOR REFERENCIAL OPERACIONES GRATUITAS", formats['boldbord'] )
			worksheet.merge_range(4,36,6,36,u"VALOR FOB DOLARES", formats['boldbord'] )
			worksheet.merge_range(4,37,6,37,u"CODIGO DE TIPO DE CARGA \n \n 1 .- Carga automática \n2 .- Carga masiva \n 3.- Registro individual", formats['boldbord'] )
			worksheet.merge_range(4,38,6,38,u"TIPO DE OPERACIÓN", formats['boldbord'] )
			x = 7

			for line in self.env['account.sunat.sire.sale.data'].search([]):
				worksheet.write(x,0,line.desEstadoComprobante if line.desEstadoComprobante else '' ,formats['especial1'])
				worksheet.write(x,1,line.codCar if line.codCar else '' ,formats['especial1'])
				worksheet.write(x,2,line.perPeriodoTributario if line.perPeriodoTributario else '' ,formats['especial1'])
				worksheet.write(x,3,line.fecEmision if line.fecEmision else '' ,formats['dateformat'])
				worksheet.write(x,4,line.fecVencPag if line.fecVencPag else '' ,formats['dateformat'])
				worksheet.write(x,5,line.codTipoCDP if line.codTipoCDP else '' ,formats['especial1'])
				worksheet.write(x,6,line.numSerieCDP if line.numSerieCDP else '' ,formats['especial1'])
				worksheet.write(x,7,line.numCDP if line.numCDP else '' ,formats['especial1'])
				worksheet.write(x,8,'' ,formats['especial1'])
				worksheet.write(x,9,line.codTipoDocIdentidad if line.codTipoDocIdentidad else '' ,formats['especial1'])
				worksheet.write(x,10,line.numDocIdentidad if line.numDocIdentidad else '' ,formats['especial1'])
				worksheet.write(x,11,line.nomRazonSocialCliente if line.nomRazonSocialCliente else '' ,formats['especial1'])
				worksheet.write(x,12,line.mtoValFactExpo if line.mtoValFactExpo else 0,formats['numberdos'])
				worksheet.write(x,13,line.mtoBIGravada if line.mtoBIGravada else 0,formats['numberdos'])
				worksheet.write(x,14,line.mtoDsctoBI if line.mtoDsctoBI else 0,formats['numberdos'])
				worksheet.write(x,15,line.mtoIGV if line.mtoIGV else 0,formats['numberdos'])
				worksheet.write(x,16,line.mtoDsctoIGV if line.mtoDsctoIGV else 0,formats['numberdos'])
				worksheet.write(x,17,line.mtoExonerado if line.mtoExonerado else 0,formats['numberdos'])
				worksheet.write(x,18,line.mtoInafecto if line.mtoInafecto else 0,formats['numberdos'])
				worksheet.write(x,19,line.mtoISC if line.mtoISC else 0,formats['numberdos'])
				worksheet.write(x,20,line.mtoBIIvap if line.mtoBIIvap else 0,formats['numberdos'])
				worksheet.write(x,21,line.mtoIvap if line.mtoIvap else 0,formats['numberdos'])
				worksheet.write(x,22,line.mtoIcbp if line.mtoIcbp else 0,formats['numberdos'])
				worksheet.write(x,23,line.mtoOtrosTrib if line.mtoOtrosTrib else 0,formats['numberdos'])
				worksheet.write(x,24,line.mtoTotalCP if line.mtoTotalCP else 0,formats['numberdos'])
				worksheet.write(x,25,line.codMoneda if line.codMoneda else '' ,formats['especial1'])
				worksheet.write(x,26,line.mtoTipoCambio if line.mtoTipoCambio else 0,formats['numbercuatro'])
				worksheet.write(x,27,line.fecEmisionMod if line.fecEmisionMod else '' ,formats['dateformat'])
				worksheet.write(x,28,line.codTipoCDPMod if line.codTipoCDPMod else '' ,formats['especial1'])
				worksheet.write(x,29,line.numSerieCDPMod if line.numSerieCDPMod else '' ,formats['especial1'])
				worksheet.write(x,30,line.numCDPMod if line.numCDPMod else '' ,formats['especial1'])
				worksheet.write(x,31,'' ,formats['especial1'])
				worksheet.write(x,32,'' ,formats['especial1'])
				worksheet.write(x,33,line.mtoPorcParticipacion if line.mtoPorcParticipacion else 0,formats['numberdos'])
				worksheet.write(x,34,line.mtoValorFob if line.mtoValorFob else 0,formats['numberdos'])
				worksheet.write(x,35,line.mtoValorOpGratuitas if line.mtoValorOpGratuitas else 0,formats['numberdos'])
				worksheet.write(x,36,line.mtoValorFobDolar if line.mtoValorFobDolar else 0,formats['numberdos'])
				worksheet.write(x,37,line.codTipoCarga if line.codTipoCarga else '' ,formats['especial1'])
				worksheet.write(x,38,line.indTipoOperacion if line.indTipoOperacion else '' ,formats['especial1'])

				x += 1

			widths = [9,27,8,10,10,6,8,9,8,7,11,90,10,12,12,13,11,11,12,11,11,11,11,11,14,7,7,11,7,10,15,20,13,10,11,11,11,14,30]
			worksheet = ReportBase.resize_cells(worksheet,widths)
			workbook.close()

			f = open(direccion +'SIREVENTAS.xlsx', 'rb')
			return self.env['popup.it'].get_file('REGISTRO DE VENTAS - RVIE SUNAT %s %s.xlsx'%(self.company_id.partner_id.vat,self.period_id.code),base64.encodebytes(b''.join(f.readlines())))

	
	def get_ventas_2(self):
		return self.get_sire(2,"v")
	
	def get_ventas_sire_excel_2(self):
		return self.get_excel_sire(2,"v")

	def get_ventas_3(self):
		return self.get_sire(3,"v")
	
	def get_ventas_sire_excel_3(self):
		return self.get_excel_sire(3,"v")

	def get_ventas_4(self):
		return self.get_sire(4,"v")
	
	def get_ventas_sire_excel_4(self):
		return self.get_excel_sire(4,"v")

	def get_ventas_5(self):
		return self.get_sire(5,"v")
	
	def get_ventas_sire_excel_5(self):
		return self.get_excel_sire(5,"v")
	########## Compras ##########
	
	def get_compras_sire_1(self):
		data = []
		#if not self.document_file:
		#	raise UserError(u'El archivo es obligatorio')
		#zip_data = base64.b64decode(self.document_file)
		#with zipfile.ZipFile(io.BytesIO(zip_data), 'r') as zip_ref:
		#	if self.name_file.replace(".zip",".txt") in zip_ref.namelist():
		txt_data = base64.b64decode(self.document_file)
		txt_data_str = txt_data.decode('utf-8')
		lines = txt_data_str.split('\n')
		data = []
		for l in lines:
			data.append(l.split('|'))
		
		data.pop(0)
		data.pop(len(data)-1)

		from xlsxwriter.workbook import Workbook
		from xlsxwriter.utility import xl_rowcol_to_cell

		ReportBase = self.env['report.base']

		direccion = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'SIRECOMPRAS.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		formats['boldbord'].set_font_size(8)

		import importlib
		import sys
		importlib.reload(sys)

		worksheet = workbook.add_worksheet("RCE - COMPRAS")

		worksheet.merge_range(1,0,1,8, "REGISTRO DE COMPRAS - RCE SUNAT%s %s"%(self.company_id.partner_id.vat,self.period_id.code), formats['especial5'] )

		#CABECERA
		worksheet.merge_range(4,0,6,0,"ESTADO DEL COMPROBANTE", formats['boldbord'] )
		worksheet.merge_range(4,1,6,1,"CAR SUNAT", formats['boldbord'] )
		worksheet.merge_range(4,2,4,9,"INFORMACIÓN RESPECTO AL COMPROBANTE DE PAGO UTILIZADO", formats['boldbord'] )
		worksheet.merge_range(5,2,6,2,"PERIODO TRIBUTARIO", formats['boldbord'] )
		worksheet.merge_range(5,3,6,3,u"FECHA DE EMISIÓN", formats['boldbord'] )
		worksheet.merge_range(5,4,6,4,"FECHA DE VENCIMIENTO O PAGO", formats['boldbord'] )
		worksheet.merge_range(5,5,6,5,"TIPO DE COMPROB.", formats['boldbord'] )
		worksheet.merge_range(5,6,6,6,"SERIE", formats['boldbord'] )
		worksheet.merge_range(5,7,6,7,u"AÑO DE EMISIÓN DE LA DAM", formats['boldbord'] )
		worksheet.merge_range(5,8,6,8,u"NÚMERO", formats['boldbord'] )
		worksheet.merge_range(5,9,6,9,u"NÚMERO / FINAL", formats['boldbord'] )
		worksheet.merge_range(4,10,4,12,u"INFORMACIÓN DEL CLIENTE", formats['boldbord'] )
		worksheet.merge_range(5,10,5,11,u"DOCUMENTO DE IDENTIDAD", formats['boldbord'] )
		worksheet.write(6,10,"TIPO DE DOCUMENTO" ,formats['boldbord'])
		worksheet.write(6,11,u"NÚMERO DE DOCUMENTO" ,formats['boldbord'])
		worksheet.merge_range(5,12,6,12,u"DENOMINACIÓN O RAZÓN SOCIAL / APELLIDOS Y NOMBRES", formats['boldbord'] )

		worksheet.merge_range(4,13,5,14,u"ADQUISICIONES GRAVADAS DESTINADAS A OPERACIONES GRAVADAS Y/O DE EXPORTACION", formats['boldbord'] )
		worksheet.write(6,13,u"BASE IMPONIBLE", formats['boldbord'] )
		worksheet.write(6,14,u"IGV", formats['boldbord'] )

		worksheet.merge_range(4,15,5,16,u"ADQUISICIONES GRAVADAS DESTINADAS A OPERACIONES GRAVADAS Y/O DE EXPORTACION Y A  OPERACIONES NO GRAVADAS", formats['boldbord'] )
		worksheet.write(6,15,u"BASE IMPONIBLE", formats['boldbord'] )
		worksheet.write(6,16,u"IGV", formats['boldbord'] )

		worksheet.merge_range(4,17,5,18,u"ADQUISICIONES GRAVADAS DESTINADAS A OPERACIONES NO GRAVADAS", formats['boldbord'] )
		worksheet.write(6,17,u"BASE IMPONIBLE", formats['boldbord'] )
		worksheet.write(6,18,u"IGV", formats['boldbord'] )

		worksheet.merge_range(4,19,6,19,u"VALOR DE LAS ADQUISICIONES NO GRAVADAS", formats['boldbord'] )
		worksheet.merge_range(4,20,6,20,u"ISC", formats['boldbord'] )
		worksheet.merge_range(4,21,6,21,u"ICBPER", formats['boldbord'] )
		worksheet.merge_range(4,22,6,22,u"OTROS TRIBUTOS Y CARGOS", formats['boldbord'] )
		worksheet.merge_range(4,23,6,23,u"IMPORTE TOTAL DEL COMPROBANTE DE PAGO", formats['boldbord'] )

		worksheet.merge_range(4,24,5,25,u"MONEDA DEL COMPROBANTE", formats['boldbord'] )
		worksheet.write(6,24,u"CÓDIGO DE LA MONEDA" ,formats['boldbord'])
		worksheet.write(6,25,u"TIPO DE CAMBIO" ,formats['boldbord'])

		worksheet.merge_range(4,26,5,30,u"REFERENCIA DEL COMPROBANTE DE PAGO ORIGINAL QUE SE MODIFICA", formats['boldbord'] )
		worksheet.write(6,26,u"FECHA" ,formats['boldbord'])
		worksheet.write(6,27,u"TIPO" ,formats['boldbord'])
		worksheet.write(6,28,u"SERIE" ,formats['boldbord'])
		worksheet.write(6,29,u"COD DE LA DAM \n O DE LA DSI" ,formats['boldbord'])
		worksheet.write(6,30,u"NÚMERO" ,formats['boldbord'])

		worksheet.merge_range(4,31,6,31,u"CLASIFICACION DE BIENES Y SERVICIOS \n > 1,500 UIT en el ejercicio anterior", formats['boldbord'] )
		worksheet.merge_range(4,32,5,33,u"OPERADORES O PARTÍCIPES DE LAS SOCIEDADES IRREGULARES, CONSORCIOS, JOINT VENTURES U OTRAS FORMAS DE CONTRATOS DE COLABORACIÓN EMPRESARIAL", formats['boldbord'] )
		worksheet.write(6,32,u"ID PROYECTO OPERADORES/ PARTÍCIPES" ,formats['boldbord'])
		worksheet.write(6,33,u"% DE PARTICIPACIÓN EN EL CONTRATO O PROYECTO" ,formats['boldbord'])

		worksheet.merge_range(4,34,6,34,u"IMPUESTO MATERIA DE BENEFICIO LEY 31053", formats['boldbord'] )
		worksheet.merge_range(4,35,6,35,u"CAR CP A MODIFICAR EN AJUSTES POSTERIORES O INDICADOR DE EXCLUSION O INCLUSION", formats['boldbord'] )
		worksheet.merge_range(4,36,6,36,u"DETRACCION", formats['boldbord'] )
		worksheet.merge_range(4,37,6,37,u"TIPO DE NOTA", formats['boldbord'] )
		worksheet.merge_range(4,38,6,38,u"INDICADOR DE INFORMACIÓN INCOMPLETA", formats['boldbord'] )
		x = 7

		for line in data:
			worksheet.write(x,0,'ACTIVO' if line[39] == '1' else '' ,formats['especial1'])
			worksheet.write(x,1,line[3] if line[3] else '' ,formats['especial1'])
			worksheet.write(x,2,line[2] if line[2] else '' ,formats['especial1'])
			worksheet.write(x,3,line[4] if line[4] else '' ,formats['dateformat'])
			worksheet.write(x,4,line[5] if line[5] else '' ,formats['dateformat'])
			worksheet.write(x,5,line[6] if line[6] else '' ,formats['especial1'])
			worksheet.write(x,6,line[7] if line[7] else '' ,formats['especial1'])
			worksheet.write(x,7,line[8] if line[8] else '' ,formats['especial1'])
			worksheet.write(x,8,line[9] if line[9] else '' ,formats['especial1'])
			worksheet.write(x,9,line[10] if line[10] else '' ,formats['especial1'])
			worksheet.write(x,10,line[11] if line[11] else '' ,formats['especial1'])
			worksheet.write(x,11,line[12] if line[12] else '' ,formats['especial1'])
			worksheet.write(x,12,line[13] if line[13] else '',formats['especial1'])
			worksheet.write(x,13,line[14] if line[14] else 0,formats['numberdos'])
			worksheet.write(x,14,line[15] if line[15] else 0,formats['numberdos'])
			worksheet.write(x,15,line[16] if line[16] else 0,formats['numberdos'])
			worksheet.write(x,16,line[17] if line[17] else 0,formats['numberdos'])
			worksheet.write(x,17,line[18] if line[18] else 0,formats['numberdos'])
			worksheet.write(x,18,line[19] if line[19] else 0,formats['numberdos'])
			worksheet.write(x,19,line[20] if line[20] else 0,formats['numberdos'])
			worksheet.write(x,20,line[21] if line[21] else 0,formats['numberdos'])
			worksheet.write(x,21,line[22] if line[22] else 0,formats['numberdos'])
			worksheet.write(x,22,line[23] if line[23] else 0,formats['numberdos'])
			worksheet.write(x,23,line[24] if line[24] else 0,formats['numberdos'])
			worksheet.write(x,24,line[25] if line[25] else '' ,formats['especial1'])
			worksheet.write(x,25,line[26] if line[26] else 0  ,formats['numbercuatro'])
			worksheet.write(x,26,line[27] if line[27] else '' ,formats['dateformat'])
			worksheet.write(x,27,line[28] if line[28] else '' ,formats['especial1'])
			worksheet.write(x,28,line[29] if line[29] else '' ,formats['especial1'])
			worksheet.write(x,29,line[30] if line[30] else '' ,formats['especial1'])
			worksheet.write(x,30,line[31] if line[31] else '' ,formats['especial1'])
			worksheet.write(x,31,line[32] if line[32] else 0  ,formats['numberdos'])
			worksheet.write(x,32,line[33] if line[33] else '' ,formats['especial1'])
			worksheet.write(x,33,line[34] if line[34] else 0,formats['numberdos'])
			worksheet.write(x,34,line[35] if line[35] else 0,formats['numberdos'])
			worksheet.write(x,35,line[36] if line[36] else '',formats['especial1'])
			worksheet.write(x,36,line[37] if line[37] else 0,formats['numberdos'])
			worksheet.write(x,37,line[38] if line[38] else '' ,formats['especial1'])
			worksheet.write(x,38,line[40] if line[40] else '' ,formats['especial1'])

			x += 1

		widths = [12,28,11,10,12,10,6,9,13,12,9,12,54,10,8,10,8,10,8,12,7,11,12,19,10,6,11,6,9,8,11,15,10,10,11,20,10,10,12]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()

		f = open(direccion +'SIRECOMPRAS.xlsx', 'rb')
		return self.env['popup.it'].get_file('REGISTRO DE COMPRAS - RCE SUNAT %s %s.xlsx'%(self.company_id.partner_id.vat,self.period_id.code),base64.encodebytes(b''.join(f.readlines())))
		
		#raise UserError(str(data))

	def get_compras_2(self):
		return self.get_sire(2,"c")
	
	def get_compras_sire_excel_2(self):
		return self.get_excel_sire(2,"c")
	
	def get_compras_3(self):
		return self.get_sire(3,"c")

	def get_compras_4(self):
		return self.get_sire(4,"c")
	
	def get_compras_sire_excel_4(self):
		return self.get_excel_sire(4,"c")

	def get_compras_5(self):
		return self.get_sire(5,"c")
	
	def get_compras_sire_excel_5(self):
		return self.get_excel_sire(5,"c")

	def get_compras_6(self):
		return self.get_sire(6,"c")
	
	def get_compras_sire_excel_6(self):
		return self.get_excel_sire(6,"c")

	def get_compras_7(self):
		return self.get_sire(7,"c")
	
	def get_compras_sire_excel_7(self):
		return self.get_excel_sire(7,"c")

	def get_compras_8(self):
		return self.get_sire(8,"c")
	
	def get_compras_sire_excel_8(self):
		return self.get_excel_sire(8,"c")

	def get_excel_sire(self,nro,type):
		ReportBase = self.env['report.base']
		sql = self.get_sql_sire(nro,type)
		self.env.cr.execute(sql)
		columns = []
		for c,col in enumerate(self.env.cr.description):
			columns.append('CAMPO %d'%(c+1))
		for l in BOOK_SIRE:
			if l["nro"] == nro and l["type"] == type:
				name_file = l["name"]
		workbook = ReportBase.get_excel_sql_export(sql,columns)
		return self.env['popup.it'].get_file('%s.xlsx'%name_file,workbook)

	def get_sire(self,nro,type):
		
		sql = self.get_sql_sire(nro,type)
		self.env.cr.execute(sql)
		sql = "COPY (%s) TO STDOUT WITH %s" % (sql, "CSV DELIMITER '|'")
	
		output = BytesIO()
		self.env.cr.copy_expert(sql, output)
		
		csv_content = output.getvalue().decode('utf-8')
		csv_lines = csv_content.split('\n')
		csv_lines.pop(len(csv_lines)-1)
		csv_lines_with_cr = [line + '\r' for line in csv_lines]
		csv_content_with_cr = '\n'.join(csv_lines_with_cr)
		csv_content_with_cr += '\n'
		res = base64.b64encode(csv_content_with_cr.encode('utf-8'))
		#res = base64.b64encode(output.getvalue())

		output.close()
		name_doc = self.get_nomenclatura(nro,type,res)

		
		res = res if res else base64.encodestring(b"== Sin Registros ==")
		name_zip = name_doc.replace(".txt",".zip")
		with zipfile.ZipFile(name_zip, 'w') as archivo_zip:
			archivo_zip.writestr(name_doc,base64.b64decode(res).decode('utf-8'))

		with open(name_zip, 'rb') as archivo:
			archivo_binario = archivo.read()
		export_file = base64.b64encode(archivo_binario)

		return self.env['popup.it'].get_file(name_zip,export_file)
	
	def get_nomenclatura(self,nro,type,res):
		ruc = self.company_id.partner_id.vat
		mond = self.company_id.currency_id.name
		if not ruc:
			raise UserError('No configuro el RUC de su Compañia.')
		if not mond:
			raise UserError('No configuro la moneda de su Compañia.')
		valor = ("1" if len(res) > 0 else "0")
		
		###############
		name_doc = ""
		if type == "v":
			if nro == 2:
				name_doc = "LE"+ruc+str(self.period_id.date_start.year)+str('{:02d}'.format(self.period_id.date_start.month)) + "00140400021"+valor+("1" if self.company_id.currency_id.name == 'PEN' else "2") + "2.txt"
			elif nro == 3:
				name_doc = "LE"+ruc+str(self.period_id.date_start.year)+str('{:02d}'.format(self.period_id.date_start.month)) + "00140400031"+valor+("1" if self.company_id.currency_id.name == 'PEN' else "2") +"2%s.txt"%(str('{:02d}'.format(self.given_numer)))
			elif nro == 4:
				name_doc = "LE"+ruc+str(self.period_id.date_start.year)+str('{:02d}'.format(self.period_id.date_start.month)) + "00140400041"+valor+("1" if self.company_id.currency_id.name == 'PEN' else "2") +"2%s.txt"%(str('{:02d}'.format(self.given_numer)))
			elif nro == 5:
				name_doc = ruc+"-CPF-"+str(self.period_id.date_start.year)+str('{:02d}'.format(self.period_id.date_start.month))+"-"+str('{:02d}'.format(self.given_numer)) + ".txt"
			else:
				raise UserError ("EN DESARROLLO")
		else:
			if nro == 2:
				if not self.comp_pr:
					name_doc = "LE"+ruc+str(self.period_id.date_start.year)+str('{:02d}'.format(self.period_id.date_start.month)) + "00080400021"+valor+("1" if self.company_id.currency_id.name == 'PEN' else "2") + "2.txt"
				else:
					name_doc = ruc+"-COMP-"+str(self.period_id.date_start.year)+str('{:02d}'.format(self.period_id.date_start.month))+"-"+str('{:02d}'.format(self.given_numer))+".txt"
			elif nro == 3:
				if self.compl_type == '0': #ADICIONAR
					name_doc = ruc+"-CP-"+str(self.period_id.date_start.year)+str('{:02d}'.format(self.period_id.date_start.month))+"-"+str('{:02d}'.format(self.given_numer))+".txt"
				elif self.compl_type in ('1','2'): #EXCLUIR e INCLUIR
					name_doc = ruc+"-RCEINEX-"+str(self.period_id.date_start.year)+str('{:02d}'.format(self.period_id.date_start.month))+"-"+str('{:02d}'.format(self.given_numer))+".txt"
			elif nro == 4:
				name_doc = "LE"+ruc+str(self.period_id.date_start.year)+str('{:02d}'.format(self.period_id.date_start.month)) + "00080400031"+valor+("1" if self.company_id.currency_id.name == 'PEN' else "2") + "2%s.txt"%(str('{:02d}'.format(self.given_numer)))
			elif nro == 5:
				name_doc = "LE"+ruc+str(self.period_id.date_start.year)+str('{:02d}'.format(self.period_id.date_start.month)) + "00080400041"+valor+("1" if self.company_id.currency_id.name == 'PEN' else "2") + "2%s.txt"%(str('{:02d}'.format(self.given_numer)))
			elif nro == 6:
				name_doc = "LE"+ruc+str(self.period_id.date_start.year)+str('{:02d}'.format(self.period_id.date_start.month)) + "00080500001"+valor+("1" if self.company_id.currency_id.name == 'PEN' else "2") + "2.txt"
			elif nro == 7:
				name_doc = "LE"+ruc+str(self.period_id.date_start.year)+str('{:02d}'.format(self.period_id.date_start.month)) + "00080500031"+valor+("1" if self.company_id.currency_id.name == 'PEN' else "2") + "2%s.txt"%(str('{:02d}'.format(self.given_numer)))
			elif nro == 8:
				name_doc = "LE"+ruc+str(self.period_id.date_start.year)+str('{:02d}'.format(self.period_id.date_start.month)) + "00080500041"+valor+("1" if self.company_id.currency_id.name == 'PEN' else "2") + "2%s.txt"%(str('{:02d}'.format(self.given_numer)))
			else:
				raise UserError ("EN DESARROLLO")
		return name_doc
	
	def get_sql_sire(self,nro,type):
		sql = ""
		if type == "v":
			if nro in [1,2,5]:
				sql = self.sql_sire_1_2_sale(self.period_id.date_start,self.period_id.date_end,self.company_id,nro == 5)
			elif nro in [3]:
				sql = self.sql_sire_3_sale(self.period_id.date_start,self.period_id.date_end,self.company_id)
			elif nro in [4]:
				sql = self.sql_sire_4_sale(self.period_id.date_start,self.period_id.date_end,self.company_id)
			else:
				raise UserError ("EN DESARROLLO")
		else:
			if nro in [1,2]:
				sql = self.sql_sire_2_purchase(self.period_id.date_start,self.period_id.date_end,self.company_id)
			elif nro in [3]:
				sql = self.sql_sire_3_purchase(self.period_id.date_start,self.period_id.date_end,self.company_id)
			elif nro in [4]:
				sql = self.sql_sire_4_purchase(self.period_id.date_start,self.period_id.date_end,self.company_id)
			elif nro in [5]:
				sql = self.sql_sire_5_purchase(self.period_id.date_start,self.period_id.date_end,self.company_id)
			#####REVISAR
			elif nro in [6]:
				sql = self.sql_sire_6_purchase(self.period_id.date_start,self.period_id.date_end,self.company_id)
			elif nro in [7]:
				sql = self.sql_sire_7_purchase(self.period_id.date_start,self.period_id.date_end,self.company_id)
			elif nro in [8]:
				sql = self.sql_sire_8_purchase(self.period_id.date_start,self.period_id.date_end,self.company_id)
			#####REVISAR
			else:
				raise UserError ("EN DESARROLLO")
		return sql
	
	def sql_sire_1_2_sale(self,date_from,date_to,company_id,cpf=False):
		sql = """SELECT T.* FROM (SELECT 
				'{ruc}' as campo1,
				'{company_name}' as campo2,
				vst_v.periodo as campo3,
				NULL as campo4,
				TO_CHAR(vst_v.fecha_e :: DATE, 'dd/mm/yyyy') as campo5,
				NULL as campo6,
				vst_v.td as campo7,
				vst_v.serie AS campo8,
				ltrim(vst_v.numero, '0') AS campo9,
				NULL as campo10,
				vst_v.tdp AS campo11,
				vst_v.docp AS campo12,
				vst_v.namep AS campo13,
				CASE
					WHEN vst_v.exp is not null THEN TRUNC(vst_v.exp,2)
					ELSE TRUNC(0,2)
				END AS campo14,
				CASE
					WHEN vst_v.td in ('07','87') and vst_v.f_doc_m < '{date_from}'::date THEN TRUNC(0,2)
					ELSE TRUNC(vst_v.venta_g,2)
				END AS campo15,
				CASE
					WHEN vst_v.td in ('07','87') and vst_v.f_doc_m < '{date_from}'::date THEN TRUNC(vst_v.venta_g,2)
					ELSE TRUNC(0,2)
				END AS campo16,
				CASE
					WHEN vst_v.td in ('07','87') and vst_v.f_doc_m < '{date_from}'::date THEN TRUNC(0,2)
					ELSE TRUNC(vst_v.igv_v,2)
				END AS campo17,
				CASE
					WHEN vst_v.td in ('07','87') and vst_v.f_doc_m < '{date_from}'::date THEN TRUNC(vst_v.igv_v,2)
					ELSE TRUNC(0,2)
				END AS campo18,
				CASE
					WHEN vst_v.exo is not null THEN TRUNC(vst_v.exo,2)
					ELSE TRUNC(0,2)
				END AS campo19,
				CASE
					WHEN vst_v.inaf is not null THEN TRUNC(vst_v.inaf,2)
					ELSE TRUNC(0,2)
				END AS campo20,
				CASE
					WHEN vst_v.isc_v is not null THEN TRUNC(vst_v.isc_v,2)
					ELSE TRUNC(0,2)
				END AS campo21,
				0.00::numeric as campo22,
				0.00::numeric as campo23,
				CASE
					WHEN vst_v.icbper is not null THEN TRUNC(vst_v.icbper,2)
					ELSE TRUNC(0,2)
				END AS campo24,
				CASE
					WHEN vst_v.otros_v is not null THEN TRUNC(vst_v.otros_v,2)
					ELSE TRUNC(0,2)
				END AS campo25,
				CASE
					WHEN vst_v.total is not null THEN TRUNC(vst_v.total,2)
					ELSE TRUNC(0,2)
				END AS campo26,
				vst_v.name AS campo27,
				vst_v.currency_rate::numeric(12,3) as campo28,
				CASE
					WHEN vst_v.f_doc_m is not null THEN TO_CHAR(vst_v.f_doc_m :: DATE, 'dd/mm/yyyy')
					ELSE NULL
				END AS campo29,
				CASE
					WHEN vst_v.td_doc_m is not null THEN vst_v.td_doc_m
					ELSE NULL
				END AS campo30,
				CASE
					WHEN vst_v.serie_m is not null and vst_v.serie_m <> '' THEN vst_v.serie_m
				END AS campo31,
				CASE
					WHEN vst_v.numero_m is not null and vst_v.numero_m <> '' THEN vst_v.numero_m
					ELSE NULL
				END AS campo32,
				NULL as campo33,
				NULL AS campo34,
				0 as campo35,
				NULL as campo36,
				NULL as campo37,
				NULL as campo38,
				NULL as campo39,
				NULL as campo40,
				NULL as campo41
				FROM get_ventas_1_1('{date_from}', '{date_to}', {company_id},'pen') vst_v
				LEFT JOIN account_move am ON am.id = vst_v.am_id
				{sql_cpf}
				)T
			""".format(
			ruc = company_id.partner_id.vat,
			company_name = company_id.partner_id.name,
			date_from = date_from.strftime('%Y/%m/%d'),
			date_to = date_to.strftime('%Y/%m/%d'),
			company_id = company_id.id,
			sql_cpf = "WHERE am.c_sire = TRUE" if cpf else ""
			)
		return sql
	
	def sql_sire_3_sale(self,date_from,date_to,company_id):
		sql = """SELECT T.* FROM (SELECT 
				'{ruc}' as campo1,
				'{company_name}' as campo2,
				vst_v.periodo as campo3,
				NULL as campo4,
				TO_CHAR(vst_v.fecha_e :: DATE, 'dd/mm/yyyy') as campo5,
				case when vst_v.td = '14' then TO_CHAR(vst_v.fecha_v :: DATE, 'dd/mm/yyyy') else NULL end as campo6,
				vst_v.td as campo7,
				vst_v.serie AS campo8,
				vst_v.numero AS campo9,
				NULL as campo10,
				vst_v.tdp AS campo11,
				vst_v.docp AS campo12,
				vst_v.namep AS campo13,
				CASE
					WHEN vst_v.exp is not null THEN TRUNC(vst_v.exp,2)
					ELSE TRUNC(0,2)
				END AS campo14,
				CASE
					WHEN vst_v.td in ('07','87') and vst_v.f_doc_m < '{date_from}'::date THEN TRUNC(0,2)
					ELSE TRUNC(vst_v.venta_g,2)
				END AS campo15,
				CASE
					WHEN vst_v.td in ('07','87') and vst_v.f_doc_m < '{date_from}'::date THEN TRUNC(vst_v.venta_g,2)
					ELSE TRUNC(0,2)
				END AS campo16,
				CASE
					WHEN vst_v.td in ('07','87') and vst_v.f_doc_m < '{date_from}'::date THEN TRUNC(0,2)
					ELSE TRUNC(vst_v.igv_v,2)
				END AS campo17,
				CASE
					WHEN vst_v.td in ('07','87') and vst_v.f_doc_m < '{date_from}'::date THEN TRUNC(vst_v.igv_v,2)
					ELSE TRUNC(0,2)
				END AS campo18,
				CASE
					WHEN vst_v.exo is not null THEN TRUNC(vst_v.exo,2)
					ELSE TRUNC(0,2)
				END AS campo19,
				CASE
					WHEN vst_v.inaf is not null THEN TRUNC(vst_v.inaf,2)
					ELSE TRUNC(0,2)
				END AS campo20,
				CASE
					WHEN vst_v.isc_v is not null THEN TRUNC(vst_v.isc_v,2)
					ELSE TRUNC(0,2)
				END AS campo21,
				0 as campo22,
				0 as campo23,
				CASE
					WHEN vst_v.icbper is not null THEN TRUNC(vst_v.icbper,2)
					ELSE TRUNC(0,2)
				END AS campo24,
				CASE
					WHEN vst_v.otros_v is not null THEN TRUNC(vst_v.otros_v,2)
					ELSE TRUNC(0,2)
				END AS campo25,
				CASE
					WHEN vst_v.total is not null THEN TRUNC(vst_v.total,2)
					ELSE TRUNC(0,2)
				END AS campo26,
				vst_v.name AS campo27,
				vst_v.currency_rate::numeric(12,3) as campo28,
				CASE
					WHEN vst_v.f_doc_m is not null THEN TO_CHAR(vst_v.f_doc_m :: DATE, 'dd/mm/yyyy')
					ELSE NULL
				END AS campo29,
				CASE
					WHEN vst_v.td_doc_m is not null THEN vst_v.td_doc_m
					ELSE NULL
				END AS campo30,
				CASE
					WHEN vst_v.serie_m is not null and vst_v.serie_m <> '' THEN vst_v.serie_m
				END AS campo31,
				CASE
					WHEN vst_v.numero_m is not null and vst_v.numero_m <> '' THEN vst_v.numero_m
					ELSE NULL
				END AS campo32,
				NULL as campo33,
				NULL AS campo34,
				NULL AS campo35,
				NULL AS campo36,
				NULL AS campo37,
				NULL AS campo38,
				NULL AS campo39,
				NULL AS campo40,
				NULL AS campo41,
				coalesce(vst_v.docp,'')||coalesce(vst_v.td,'')||coalesce(vst_v.serie,'')||LPAD(vst_v.numero, 10, '0') AS campo42,
				NULL AS campo43
				FROM get_ventas_1_1('{date_from}', '{date_to}', {company_id},'pen') vst_v
				LEFT JOIN account_move am ON am.id = vst_v.am_id
				WHERE am.adj_sire = TRUE
				)T
			""".format(
			ruc = company_id.partner_id.vat,
			company_name = company_id.partner_id.name,
			date_from = date_from.strftime('%Y/%m/%d'),
			date_to = date_to.strftime('%Y/%m/%d'),
			company_id = company_id.id
			)
		return sql
	
	def sql_sire_4_sale(self,date_from,date_to,company_id):
		sql = """SELECT T.* FROM (SELECT 
				vst_v.periodo || '00' as campo1,
				vst_v.periodo || vst_v.libro || vst_v.voucher as campo2,
				'M' || vst_v.voucher as campo3,
				TO_CHAR(vst_v.fecha_e :: DATE, 'dd/mm/yyyy') as campo4,
				CASE
					WHEN vst_v.td = '14' THEN TO_CHAR(vst_v.fecha_v :: DATE, 'dd/mm/yyyy')
					ELSE NULL
				END AS campo5,
				vst_v.td AS campo6,
				vst_v.serie AS campo7,
				vst_v.numero AS campo8,
				CASE
					WHEN (am.campo_09_sale is not null) and (vst_v.td = '00' or vst_v.td = '03' or vst_v.td = '12' or vst_v.td = '13' or vst_v.td = '87') THEN am.campo_09_sale
					ELSE NULL
				END AS campo9,
				vst_v.tdp AS campo10,
				vst_v.docp AS campo11,
				vst_v.namep AS campo12,
				CASE
					WHEN vst_v.exp is not null THEN TRUNC(vst_v.exp,2)
					ELSE TRUNC(0,2)
				END AS campo13,
				CASE
					WHEN (am.is_descount is null or am.is_descount = False) and vst_v.venta_g is not null THEN TRUNC(vst_v.venta_g,2)
					ELSE TRUNC(0,2)
				END AS campo14,
				CASE
					WHEN (am.is_descount = True) and vst_v.venta_g is not null THEN TRUNC(vst_v.venta_g,2)
					ELSE TRUNC(0,2)
				END AS campo15,
				CASE
					WHEN (am.is_descount is null or am.is_descount = False) and vst_v.igv_v is not null THEN TRUNC(vst_v.igv_v,2)
					ELSE TRUNC(0,2)
				END AS campo16,
				CASE
					WHEN (am.is_descount = True) and vst_v.igv_v is not null THEN TRUNC(vst_v.igv_v,2)
					ELSE TRUNC(0,2)
				END AS campo17,
				CASE
					WHEN vst_v.exo is not null THEN TRUNC(vst_v.exo,2)
					ELSE TRUNC(0,2)
				END AS campo18,
				CASE
					WHEN vst_v.inaf is not null THEN TRUNC(vst_v.inaf,2)
					ELSE TRUNC(0,2)
				END AS campo19,
				CASE
					WHEN vst_v.isc_v is not null THEN TRUNC(vst_v.isc_v,2)
					ELSE TRUNC(0,2)
				END AS campo20,
				TRUNC(0,2) as campo21,
				TRUNC(0,2) as campo22,
				CASE
					WHEN vst_v.icbper is not null THEN TRUNC(vst_v.icbper,2)
					ELSE TRUNC(0,2)
				END AS campo23,
				CASE
					WHEN vst_v.otros_v is not null THEN TRUNC(vst_v.otros_v,2)
					ELSE TRUNC(0,2)
				END AS campo24,
				CASE
					WHEN vst_v.total is not null THEN TRUNC(vst_v.total,2)
					ELSE TRUNC(0,2)
				END AS campo25,
				vst_v.name AS campo26,
				vst_v.currency_rate::numeric(12,3) as campo27,
				CASE
					WHEN vst_v.f_doc_m is not null THEN TO_CHAR(vst_v.f_doc_m :: DATE, 'dd/mm/yyyy')
					ELSE NULL
				END AS campo28,
				CASE
					WHEN vst_v.td_doc_m is not null THEN vst_v.td_doc_m
					ELSE NULL
				END AS campo29,
				CASE
					WHEN vst_v.serie_m is not null OR vst_v.serie_m <> '' THEN vst_v.serie_m
					ELSE NULL
				END AS campo30,
				CASE
					WHEN vst_v.numero_m is not null THEN vst_v.numero_m
					ELSE NULL
				END AS campo31,
				NULL AS campo32,
				CASE
					WHEN am.campo_32_sale = True THEN '1'
					ELSE NULL
				END AS campo33,
				CASE
					WHEN am.campo_33_sale = True THEN '1'
					ELSE NULL
				END AS campo34,
				am.campo_34_sale AS campo35,
				NULL AS campo36
				FROM get_ventas_1_1_sunat('{date_from}','{date_to}',{company_id},'date_modify_sale') vst_v
				LEFT JOIN account_move am ON am.id = vst_v.am_id)T
				ORDER BY T.campo1, T.campo2, T.campo3
			""".format(
			date_from = date_from.strftime('%Y/%m/%d'),
			date_to = date_to.strftime('%Y/%m/%d'),
			company_id = company_id.id
			)
		return sql
	
	def sql_sire_2_purchase(self,date_from,date_to,company_id):
		sql = """SELECT T.* FROM (
			SELECT '{ruc}' as campo1,
			'{company_name}' as campo2,
			vst_c.periodo as campo3,
			NULL as campo4,
			TO_CHAR(vst_c.fecha_e :: DATE, 'dd/mm/yyyy') as campo5,
			NULL as campo6,
			vst_c.td as campo7,
			CASE
				WHEN coalesce(vst_c.serie,'') <> ''  THEN vst_c.serie
				ELSE NULL
			END AS campo8,
			vst_c.anio as campo9,
			vst_c.numero as campo10,
			am.campo_09_purchase as campo11,
			vst_c.tdp as campo12,
			vst_c.docp as campo13,
			vst_c.namep as campo14,
			TRUNC(vst_c.base1,2) as campo15,
			TRUNC(vst_c.igv1,2) as campo16,
			TRUNC(vst_c.base2,2) as campo17,
			TRUNC(vst_c.igv2,2) as campo18,
			TRUNC(vst_c.base3,2) as campo19,
			TRUNC(vst_c.igv3,2) as campo20,
			TRUNC(vst_c.cng,2) as campo21,
			TRUNC(vst_c.isc,2) as campo22,
			TRUNC(vst_c.icbper,2) as campo23,
			TRUNC(vst_c.otros,2) as campo24,
			TRUNC(vst_c.total,2) as campo25,
			vst_c.name as campo26,
			vst_c.currency_rate::numeric(12,3) as campo27,
			CASE
				WHEN vst_c.f_doc_m is not null THEN TO_CHAR(vst_c.f_doc_m :: DATE, 'dd/mm/yyyy') 
				ELSE NULL
			END AS campo28,
			CASE
				WHEN vst_c.td_doc_m is not null THEN vst_c.td_doc_m
				ELSE NULL
			END AS campo29,
			CASE
				WHEN vst_c.serie_m is not null or vst_c.serie_m <> '' THEN vst_c.serie_m
				ELSE NULL
			END AS campo30,
			CASE
				WHEN (vst_c.td_doc_m = '50' or vst_c.td_doc_m = '52') and vst_c.serie_m is not null THEN vst_c.serie_m
				ELSE NULL
			END AS campo31,
			CASE
				WHEN vst_c.numero_m is not null THEN vst_c.numero_m
				ELSE NULL
			END AS campo32,
			CASE
				WHEN am.campo_34_purchase is not null THEN am.campo_34_purchase
				ELSE NULL
			END AS campo33,
			CASE
				WHEN am.campo_35_purchase is not null THEN am.campo_35_purchase
				ELSE NULL
			END AS campo34,
			CASE
				WHEN am.participation_percent_sire is not null THEN am.participation_percent_sire
				ELSE NULL
			END AS campo35,
			CASE
				WHEN am.tax_mat_exo_igv_sire is not null THEN am.tax_mat_exo_igv_sire
				ELSE NULL
			END AS campo36,
			NULL AS campo37,
			NULL AS campo38,
			NULL AS campo39,
			NULL AS campo40,
			NULL AS campo41,
			NULL AS campo42
			from get_compras_1_1('{date_from}', '{date_to}', {company_id},'pen') vst_c
			left join account_move am on am.id = vst_c.am_id
			where am.corre_sire IS NULL)T
			ORDER BY T.campo1, T.campo2, T.campo3
				""".format(
			ruc = company_id.partner_id.vat,
			company_name = company_id.partner_id.name,
			date_from = date_from.strftime('%Y/%m/%d'),
			date_to = date_to.strftime('%Y/%m/%d'),
			company_id = company_id.id,
			)
		return sql
	
	def sql_sire_3_purchase(self,date_from,date_to,company_id):
		if self.compl_type == '0':
			sql = """SELECT T.* FROM (
				SELECT '{ruc}' as campo1,
				'{company_name}' as campo2,
				vst_c.periodo as campo3,
				NULL as campo4,
				TO_CHAR(vst_c.fecha_e :: DATE, 'dd/mm/yyyy') as campo5,
				NULL as campo6,
				vst_c.td as campo7,
				CASE
					WHEN coalesce(vst_c.serie,'') <> ''  THEN vst_c.serie
					ELSE NULL
				END AS campo8,
				vst_c.anio as campo9,
				vst_c.numero as campo10,
				am.campo_09_purchase as campo11,
				vst_c.tdp as campo12,
				vst_c.docp as campo13,
				vst_c.namep as campo14,
				TRUNC(vst_c.base1,2) as campo15,
				TRUNC(vst_c.igv1,2) as campo16,
				TRUNC(vst_c.base2,2) as campo17,
				TRUNC(vst_c.igv2,2) as campo18,
				TRUNC(vst_c.base3,2) as campo19,
				TRUNC(vst_c.igv3,2) as campo20,
				TRUNC(vst_c.cng,2) as campo21,
				TRUNC(vst_c.isc,2) as campo22,
				TRUNC(vst_c.icbper,2) as campo23,
				TRUNC(vst_c.otros,2) as campo24,
				TRUNC(vst_c.total,2) as campo25,
				vst_c.name as campo26,
				vst_c.currency_rate::numeric(12,3) as campo27,
				CASE
					WHEN vst_c.f_doc_m is not null THEN TO_CHAR(vst_c.f_doc_m :: DATE, 'dd/mm/yyyy') 
					ELSE NULL
				END AS campo28,
				CASE
					WHEN vst_c.td_doc_m is not null THEN vst_c.td_doc_m
					ELSE NULL
				END AS campo29,
				CASE
					WHEN vst_c.serie_m is not null or vst_c.serie_m <> '' THEN vst_c.serie_m
					ELSE NULL
				END AS campo30,
				CASE
					WHEN (vst_c.td_doc_m = '50' or vst_c.td_doc_m = '52') and vst_c.serie_m is not null THEN vst_c.serie_m
					ELSE NULL
				END AS campo31,
				CASE
					WHEN vst_c.numero_m is not null THEN vst_c.numero_m
					ELSE NULL
				END AS campo32,
				CASE
					WHEN am.campo_34_purchase is not null THEN am.campo_34_purchase
					ELSE NULL
				END AS campo33,
				CASE
					WHEN am.campo_35_purchase is not null THEN am.campo_35_purchase
					ELSE NULL
				END AS campo34,
				CASE
					WHEN am.participation_percent_sire is not null THEN am.participation_percent_sire
					ELSE NULL
				END AS campo35,
				CASE
					WHEN am.tax_mat_exo_igv_sire is not null THEN am.tax_mat_exo_igv_sire
					ELSE NULL
				END AS campo36,
				NULL AS campo37,
				NULL AS campo38,
				NULL AS campo39,
				NULL AS campo40,
				NULL AS campo41,
				NULL AS campo42
				from get_compras_1_1('{date_from}', '{date_to}', {company_id},'pen') vst_c
				left join account_move am on am.id = vst_c.am_id
				where am.corre_sire = '0')T
				ORDER BY T.campo1, T.campo2, T.campo3
					""".format(
				ruc = company_id.partner_id.vat,
				company_name = company_id.partner_id.name,
				date_from = date_from.strftime('%Y/%m/%d'),
				date_to = date_to.strftime('%Y/%m/%d'),
				company_id = company_id.id,
				)
		else:
			sql = """SELECT T.* FROM (
				SELECT '{ruc}' as campo1,
				'{company_name}' as campo2,
				vst_c.periodo as campo3,
				coalesce(vst_c.docp,'')||coalesce(vst_c.td,'')||coalesce(vst_c.serie,'')||LPAD(vst_c.numero, 10, '0') as campo4,
				NULL as campo5,
				NULL as campo6,
				NULL as campo7,
				NULL campo8,
				NULL as campo9,
				NULL as campo10,
				NULL as campo11,
				NULL as campo12,
				NULL as campo13,
				NULL as campo14,
				0::numeric as campo15,
				0::numeric as campo16,
				0::numeric as campo17,
				0::numeric as campo18,
				0::numeric as campo19,
				0::numeric as campo20,
				0::numeric as campo21,
				0::numeric as campo22,
				0::numeric as campo23,
				0::numeric as campo24,
				0::numeric as campo25,
				NULL as campo26,
				NULL as campo27,
				NULL AS campo28,
				NULL AS campo29,
				NULL AS campo30,
				NULL AS campo31,
				NULL AS campo32,
				NULL AS campo33,
				NULL AS campo34,
				NULL AS campo35,
				NULL AS campo36,
				'{compl_type}'::character varying AS campo37,
				NULL AS campo38,
				NULL AS campo39,
				NULL AS campo40,
				NULL AS campo41,
				NULL AS campo42
				from get_compras_1_1('{date_from}', '{date_to}', {company_id},'pen') vst_c
				left join account_move am on am.id = vst_c.am_id
				where am.corre_sire = '{compl_type}')T
				ORDER BY T.campo1, T.campo2, T.campo3
					""".format(
				ruc = company_id.partner_id.vat,
				company_name = company_id.partner_id.name,
				date_from = date_from.strftime('%Y/%m/%d'),
				date_to = date_to.strftime('%Y/%m/%d'),
				company_id = company_id.id,
				compl_type = self.compl_type
				)
		return sql
	
	def sql_sire_4_purchase(self,date_from,date_to,company_id):
		sql = """SELECT T.* FROM (
			SELECT '{ruc}' as campo1,
			'{company_name}' as campo2,
			vst_c.periodo as campo3,
			NULL as campo4,
			TO_CHAR(vst_c.fecha_e :: DATE, 'dd/mm/yyyy') as campo5,
			NULL as campo6,
			vst_c.td as campo7,
			CASE
				WHEN coalesce(vst_c.serie,'') <> ''  THEN vst_c.serie
				ELSE NULL
			END AS campo8,
			vst_c.anio as campo9,
			vst_c.numero as campo10,
			am.campo_09_purchase as campo11,
			vst_c.tdp as campo12,
			vst_c.docp as campo13,
			vst_c.namep as campo14,
			TRUNC(vst_c.base1,2) as campo15,
			TRUNC(vst_c.igv1,2) as campo16,
			TRUNC(vst_c.base2,2) as campo17,
			TRUNC(vst_c.igv2,2) as campo18,
			TRUNC(vst_c.base3,2) as campo19,
			TRUNC(vst_c.igv3,2) as campo20,
			TRUNC(vst_c.cng,2) as campo21,
			TRUNC(vst_c.isc,2) as campo22,
			TRUNC(vst_c.icbper,2) as campo23,
			TRUNC(vst_c.otros,2) as campo24,
			TRUNC(vst_c.total,2) as campo25,
			vst_c.name as campo26,
			vst_c.currency_rate::numeric(12,3) as campo27,
			CASE
				WHEN vst_c.f_doc_m is not null THEN TO_CHAR(vst_c.f_doc_m :: DATE, 'dd/mm/yyyy') 
				ELSE NULL
			END AS campo28,
			CASE
				WHEN vst_c.td_doc_m is not null THEN vst_c.td_doc_m
				ELSE NULL
			END AS campo29,
			CASE
				WHEN vst_c.serie_m is not null or vst_c.serie_m <> '' THEN vst_c.serie_m
				ELSE NULL
			END AS campo30,
			CASE
				WHEN (vst_c.td_doc_m = '50' or vst_c.td_doc_m = '52') and vst_c.serie_m is not null THEN vst_c.serie_m
				ELSE NULL
			END AS campo31,
			CASE
				WHEN vst_c.numero_m is not null THEN vst_c.numero_m
				ELSE NULL
			END AS campo32,
			CASE
				WHEN am.campo_34_purchase is not null THEN am.campo_34_purchase
				ELSE NULL
			END AS campo33,
			CASE
				WHEN am.campo_35_purchase is not null THEN am.campo_35_purchase
				ELSE NULL
			END AS campo34,
			CASE
				WHEN am.participation_percent_sire is not null THEN am.participation_percent_sire
				ELSE NULL
			END AS campo35,
			CASE
				WHEN am.tax_mat_exo_igv_sire is not null THEN am.tax_mat_exo_igv_sire
				ELSE NULL
			END AS campo36,
			coalesce(vst_c.docp,'')||coalesce(vst_c.td,'')||coalesce(vst_c.serie,'')||LPAD(vst_c.numero, 10, '0') AS campo37,
			NULL AS campo38,
			NULL AS campo39,
			NULL AS campo40,
			NULL AS campo41,
			NULL AS campo42
			from get_compras_1_1('{date_from}', '{date_to}', {company_id},'pen') vst_c
			left join account_move am on am.id = vst_c.am_id
			where am.corre_sire = '3')T
			ORDER BY T.campo1, T.campo2, T.campo3
				""".format(
			ruc = company_id.partner_id.vat,
			company_name = company_id.partner_id.name,
			date_from = date_from.strftime('%Y/%m/%d'),
			date_to = date_to.strftime('%Y/%m/%d'),
			company_id = company_id.id,
			)
		return sql
	
	def sql_sire_5_purchase(self,date_from,date_to,company_id):
		sql = """
			select T.* FROM (select vst_c.periodo || '00' as campo1,
			vst_c.periodo || vst_c.libro || vst_c.voucher as campo2,
			'M' || vst_c.voucher as campo3,
			TO_CHAR(vst_c.fecha_e :: DATE, 'dd/mm/yyyy') as campo4,
			CASE
				WHEN vst_c.td = '14' THEN TO_CHAR(vst_c.fecha_v :: DATE, 'dd/mm/yyyy')
				ELSE NULL
			END AS campo5,
			CASE
				WHEN vst_c.td is null THEN NULL
				ELSE vst_c.td
			END AS campo6,
			CASE
				WHEN vst_c.serie is not null or vst_c.serie <> '' THEN vst_c.serie
				ELSE NULL
			END AS campo7,
			CASE
				WHEN vst_c.anio is not null THEN vst_c.anio
				ELSE NULL
			END AS campo8,
			CASE
				WHEN vst_c.numero is not null THEN vst_c.numero
				ELSE NULL
			END AS campo9,
			NULL as campo10,
			vst_c.tdp as campo11,
			vst_c.docp as campo12,
			vst_c.namep as campo13,
			TRUNC(vst_c.base1,2) as campo14,
			TRUNC(vst_c.igv1,2) as campo15,
			TRUNC(vst_c.base2,2) as campo16,
			TRUNC(vst_c.igv2,2) as campo17,
			TRUNC(vst_c.base3,2) as campo18,
			TRUNC(vst_c.igv3,2) as campo19,
			TRUNC(vst_c.cng,2) as campo20,
			TRUNC(vst_c.isc,2) as campo21,
			TRUNC(vst_c.icbper,2) as campo22,
			TRUNC(vst_c.otros,2) as campo23,
			TRUNC(vst_c.total,2) as campo24,
			vst_c.name as campo25,
			vst_c.currency_rate::numeric(12,3) as campo26,
			CASE
				WHEN vst_c.f_doc_m is not null THEN TO_CHAR(vst_c.f_doc_m :: DATE, 'dd/mm/yyyy') 
				ELSE NULL
			END AS campo27,
			CASE
				WHEN vst_c.td_doc_m is not null THEN vst_c.td_doc_m
				ELSE NULL
			END AS campo28,
			CASE
				WHEN vst_c.serie_m is not null or vst_c.serie_m <> '' THEN vst_c.serie_m
				ELSE NULL
			END AS campo29,
			CASE
				WHEN (vst_c.td_doc_m = '50' or vst_c.td_doc_m = '52') and vst_c.serie_m is not null THEN vst_c.serie_m
				ELSE NULL
			END AS campo30,
			CASE
				WHEN vst_c.numero_m is not null THEN vst_c.numero_m
				ELSE NULL
			END AS campo31,
			CASE
				WHEN vst_c.fecha_det is not null THEN TO_CHAR(vst_c.fecha_det :: DATE, 'dd/mm/yyyy') 
				ELSE NULL
			END AS campo32,
			CASE
				WHEN coalesce(vst_c.comp_det,'') <> '' THEN vst_c.comp_det
				ELSE NULL
			END AS campo33,
			CASE
				WHEN am.campo_33_purchase = True THEN '1'
				ELSE NULL
			END AS campo34,
			CASE
				WHEN am.campo_34_purchase is not null THEN am.campo_34_purchase
				ELSE NULL
			END AS campo35,
			CASE
				WHEN am.campo_35_purchase is not null THEN am.campo_35_purchase
				ELSE NULL
			END AS campo36,
			NULL AS campo37,
			NULL AS campo38,
			NULL AS campo39,
			NULL AS campo40,
			CASE
				WHEN am.campo_40_purchase = True THEN '1'
				ELSE NULL
			END AS campo41,
			CASE
				WHEN am.campo_41_purchase is not null THEN am.campo_41_purchase
				ELSE NULL
			END AS campo42,
			NULL AS campo43
			from get_compras_1_1_sunat('{date_from}','{date_to}',{company_id},'date_modify_purchase') vst_c
			left join account_move am on am.id = vst_c.am_id
			WHERE am.campo_41_purchase = '9')T
			ORDER BY T.campo1, T.campo2, T.campo3
		""".format(
			date_from = date_from.strftime('%Y/%m/%d'),
			date_to = date_to.strftime('%Y/%m/%d'),
			company_id = company_id.id,
			)
		return sql
	
	def sql_sire_6_purchase(self,date_from,date_to,company_id):
		sql = """SELECT T.* FROM (select 
				vst_c.periodo as campo1,
				NULL as campo2,
				TO_CHAR(vst_c.fecha_e :: DATE, 'dd/mm/yyyy') as campo3,
				vst_c.td as campo4,
				vst_c.serie as campo5,
				vst_c.numero as campo6,
				coalesce(vst_c.cng,0.00) as campo7,
				coalesce(vst_c.otros,0.00) as campo8,
				coalesce(vst_c.total,0.00) as campo9,
				ec01.code as campo10,
				am.campo_12_purchase_nd as campo11,
				am.campo_13_purchase_nd as campo12,
				am.campo_14_purchase_nd as campo13,
				coalesce(am.campo_15_purchase_nd,0) as campo14,
				vst_c.name AS campo15,
				vst_c.currency_rate::numeric(12,3) as campo16,
				rp1.country_home_nd as campo17,
				vst_c.namep as campo18,
				rp1.home_nd as campo19,
				vst_c.docp as campo20,
				rp1.ide_nd as campo21,
				rp2.name as campo22,
				rp2.country_home_nd as campo23,
				rp1.v_con_nd as campo24,
				coalesce(am.campo_26_purchase_nd,0) as campo25,
				coalesce(am.campo_27_purchase_nd,0) as campo26,
				coalesce(am.campo_28_purchase_nd,0) as campo27,
				coalesce(am.campo_29_purchase_nd,0) as campo28,
				coalesce(am.campo_30_purchase_nd,0) as campo29,
				rp1.c_d_imp as campo30,
				am.campo_32_purchase_nd as campo31,
				am.campo_33_purchase_nd as campo32,
				am.campo_34_purchase_nd as campo33,
				CASE
					WHEN am.campo_35_purchase_nd = TRUE THEN '1'
					ELSE NULL
				END AS campo34,
				NULL AS campo35,
				NULL AS campo36
				FROM get_compras_1_1('{date_from}', '{date_to}', {company_id},'pen') vst_c
				LEFT JOIN account_move am ON am.id = vst_c.am_id
				LEFT JOIN res_partner rp1 ON rp1.id = vst_c.partner_id
				LEFT JOIN res_partner rp2 ON rp2.id = am.campo_23_purchase_nd
				LEFT JOIN l10n_latam_document_type ec01 ON ec01.id = am.campo_11_purchase_nd
				WHERE rp1.is_not_home = TRUE AND vst_c.td in ('00','91','97','98')
				and am.corre_sire IS NULL)T
				ORDER BY T.campo1, T.campo2, T.campo3
				""".format(
			date_from = date_from.strftime('%Y/%m/%d'),
			date_to = date_to.strftime('%Y/%m/%d'),
			company_id = company_id.id,
			)
		return sql
	
	def sql_sire_7_purchase(self,date_from,date_to,company_id):
		sql = """SELECT T.* FROM (select 
				vst_c.periodo as campo1,
				NULL as campo2,
				TO_CHAR(vst_c.fecha_e :: DATE, 'dd/mm/yyyy') as campo3,
				vst_c.td as campo4,
				vst_c.serie as campo5,
				vst_c.numero as campo6,
				coalesce(vst_c.cng,0.00) as campo7,
				coalesce(vst_c.otros,0.00) as campo8,
				coalesce(vst_c.total,0.00) as campo9,
				ec01.code as campo10,
				am.campo_12_purchase_nd as campo11,
				am.campo_13_purchase_nd as campo12,
				am.campo_14_purchase_nd as campo13,
				coalesce(am.campo_15_purchase_nd,0) as campo14,
				vst_c.name AS campo15,
				vst_c.currency_rate::numeric(12,3) as campo16,
				rp1.country_home_nd as campo17,
				vst_c.namep as campo18,
				rp1.home_nd as campo19,
				vst_c.docp as campo20,
				rp1.ide_nd as campo21,
				rp2.name as campo22,
				rp2.country_home_nd as campo23,
				rp1.v_con_nd as campo24,
				coalesce(am.campo_26_purchase_nd,0) as campo25,
				coalesce(am.campo_27_purchase_nd,0) as campo26,
				coalesce(am.campo_28_purchase_nd,0) as campo27,
				coalesce(am.campo_29_purchase_nd,0) as campo28,
				coalesce(am.campo_30_purchase_nd,0) as campo29,
				rp1.c_d_imp as campo30,
				am.campo_32_purchase_nd as campo31,
				am.campo_33_purchase_nd as campo32,
				am.campo_34_purchase_nd as campo33,
				CASE
					WHEN am.campo_35_purchase_nd = TRUE THEN '1'
					ELSE NULL
				END AS campo34,
				coalesce(vst_c.docp,'')||coalesce(vst_c.td,'')||coalesce(vst_c.serie,'')||LPAD(vst_c.numero, 10, '0') AS campo35,
				NULL AS campo36
				FROM get_compras_1_1('{date_from}', '{date_to}', {company_id},'pen') vst_c
				LEFT JOIN account_move am ON am.id = vst_c.am_id
				LEFT JOIN res_partner rp1 ON rp1.id = vst_c.partner_id
				LEFT JOIN res_partner rp2 ON rp2.id = am.campo_23_purchase_nd
				LEFT JOIN l10n_latam_document_type ec01 ON ec01.id = am.campo_11_purchase_nd
				WHERE rp1.is_not_home = TRUE AND vst_c.td in ('00','91','97','98')
				and am.corre_sire = '3')T
				ORDER BY T.campo1, T.campo2, T.campo3
				""".format(
			date_from = date_from.strftime('%Y/%m/%d'),
			date_to = date_to.strftime('%Y/%m/%d'),
			company_id = company_id.id,
			)
		return sql
	
	def sql_sire_8_purchase(self,date_from,date_to,company_id):
		sql = """
				select T.* FROM (select 
				vst_c.periodo || '00' as campo1,
				vst_c.periodo || vst_c.libro || vst_c.voucher as campo2,
				'M' || vst_c.voucher as campo3,
				TO_CHAR(vst_c.fecha_e :: DATE, 'dd/mm/yyyy') as campo4,
				vst_c.td AS campo5,
				vst_c.serie AS campo6,
				vst_c.numero AS campo7,
				coalesce(vst_c.cng,0) AS campo8,
				coalesce(vst_c.otros,0) AS campo9,
				coalesce(vst_c.total,0) AS campo10,
				ec01.code AS campo11,
				am.campo_12_purchase_nd AS campo12,
				am.campo_13_purchase_nd AS campo13,
				am.campo_14_purchase_nd AS campo14,
				coalesce(am.campo_15_purchase_nd,0) AS campo15,
				vst_c.name AS campo16,
				vst_c.currency_rate::numeric(12,3) as campo17,
				rp1.country_home_nd AS campo18,
				vst_c.namep as campo19,
				rp1.home_nd AS campo20,
				vst_c.docp AS campo21,
				rp2.vat AS campo22,
				rp2.name AS campo23,
				rp2.country_home_nd AS campo24,
				rp1.v_con_nd AS campo25,
				coalesce(am.campo_26_purchase_nd,0) AS campo26,
				coalesce(am.campo_27_purchase_nd,0) AS campo27,
				coalesce(am.campo_28_purchase_nd,0) AS campo28,
				coalesce(am.campo_29_purchase_nd,0) AS campo29,
				coalesce(am.campo_30_purchase_nd,0) AS campo30,
				rp1.c_d_imp AS campo31,
				am.campo_32_purchase_nd AS campo32,
				am.campo_33_purchase_nd AS campo33,
				am.campo_34_purchase_nd AS campo34,
				CASE
					WHEN am.campo_35_purchase_nd = TRUE THEN '1'
					ELSE NULL
				END AS campo35,
				am.campo_41_purchase AS campo36,
				NULL AS campo37
				from get_compras_1_1_sunat('{date_from}','{date_to}',{company_id},'date_modify_purchase') vst_c
				LEFT JOIN account_move am ON am.id = vst_c.am_id
				LEFT JOIN res_partner rp1 ON rp1.id = vst_c.partner_id
				LEFT JOIN res_partner rp2 ON rp2.id = am.campo_23_purchase_nd
				LEFT JOIN l10n_latam_document_type ec01 ON ec01.id = am.campo_11_purchase_nd
				WHERE vst_c.td in ('00','91','97','98') and rp1.is_not_home = TRUE
				AND am.campo_41_purchase = '9')T
				ORDER BY T.campo1, T.campo2, T.campo3
		""".format(
			date_from = date_from.strftime('%Y/%m/%d'),
			date_to = date_to.strftime('%Y/%m/%d'),
			company_id = company_id.id,
			)
		return sql
	
	def get_data_from_api_sale(self):
		#obj_query = self.env['account.query.sunat']
		param = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1)
		if not param:
			raise UserError(u'No existen Parametros Principales de Contabilidad para su Compañía')
		
		if not param.sire_client_id or not param.sire_client_secret or not param.sire_username or not param.sire_password:
			raise UserError(u'No estan configuradas las credenciales generadas en la página de SIRE en Parametros Principales de Contabilidad para su Compañía')

		today = datetime.now()

		if not param.sire_token_expire or today>param.sire_token_expiration_date:
			params = {"grant_type" : u"password",
					"scope": u"https://api-sire.sunat.gob.pe",
					"client_id": param.sire_client_id,
					"client_secret": param.sire_client_secret,
					"username": (self.company_id.partner_id.vat or '') + (param.sire_username or ''),
					"password": param.sire_password}

			
			url = 'https://api-seguridad.sunat.gob.pe/v1/clientessol/{client_id}/oauth2/token/'.format(client_id = param.sire_client_id)
			
			headers = requests.utils.default_headers()
			headers['Content-Type'] = 'application/x-www-form-urlencoded'
			headers['User-Agent'] = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'
			try:
				r = requests.post(url, headers=headers, data=params)
				arr2 = json.loads(r.text)
				if 'access_token' in arr2.keys():
					param.sire_token_expire = arr2['access_token']
					param.sire_token_generation_date = today
					param.sire_token_expiration_date = today + timedelta(seconds=int(arr2['expires_in']))
			except Exception as err:
				raise UserError(err)
		
		params = {
				'page': 1,
				'perPage': 1000
			}
		
		url = 'https://api-sire.sunat.gob.pe/v1/contribuyente/migeigv/libros/rvie/propuesta/web/propuesta/{period}/comprobantes'.format(period = self.period_id.code)
		headers = requests.utils.default_headers()
		headers['Content-Type'] = 'application/json'
		headers['Accept'] = 'application/json'
		headers['Authorization'] = 'Bearer ' + param.sire_token_expire 
		headers['User-Agent'] = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'
		arr2={}
		try:
			r = requests.get(url, headers=headers, params=params)
			arre = r.text.replace("'",'"')
			arr2 = json.loads(arre)

		except Exception as err:
			raise UserError(err)
		if 'registros' in arr2.keys():
			self.env['account.sunat.sire.sale.data'].unlink()
			for reg in arr2['registros']:
				values = {
					'sire_id': reg['id'],
					'perPeriodoTributario': reg['perPeriodoTributario'],
					'codCar': reg['codCar'],
					'codTipoCDP': reg['codTipoCDP'],
					'numSerieCDP': reg['numSerieCDP'],
					'numCDP': reg['numCDP'],
					'codTipoCarga': reg['codTipoCarga'],
					'codSituacion': reg['codSituacion'],
					'fecEmision':  datetime.strptime(reg['fecEmision'], '%d/%m/%Y').date() if 'fecEmision'  in reg.keys() else None,
					'fecVencPag': datetime.strptime(reg['fecVencPag'], '%d/%m/%Y').date() if 'fecVencPag' in reg.keys() else None,
					'codTipoDocIdentidad': reg['codTipoDocIdentidad'],
					'numDocIdentidad': reg['numDocIdentidad'],
					'nomRazonSocialCliente': reg['nomRazonSocialCliente'],
					'mtoValFactExpo': reg['mtoValFactExpo'],
					'mtoBIGravada': reg['mtoBIGravada'],
					'mtoDsctoBI': reg['mtoDsctoBI'],
					'mtoIGV': reg['mtoIGV'],
					'mtoDsctoIGV': reg['mtoDsctoIGV'],
					'mtoExonerado': reg['mtoExonerado'],
					'mtoInafecto': reg['mtoInafecto'],
					'mtoISC': reg['mtoISC'],
					'mtoBIIvap': reg['mtoBIIvap'],
					'mtoIvap': reg['mtoIvap'],
					'mtoIcbp': reg['mtoIcbp'],
					'mtoOtrosTrib': reg['mtoOtrosTrib'],
					'mtoTotalCP': reg['mtoTotalCP'],
					'codMoneda': reg['codMoneda'],
					'mtoTipoCambio': reg['mtoTipoCambio'],
					'codEstadoComprobante': reg['codEstadoComprobante'],
					'desEstadoComprobante': reg['desEstadoComprobante'],
					'indOperGratuita': reg['indOperGratuita'],
					'mtoValorOpGratuitas': reg['mtoValorOpGratuitas'],
					'mtoValorFob': reg['mtoValorFob'],
					'indTipoOperacion': reg['indTipoOperacion'] if 'indTipoOperacion' in reg.keys() else None,
					'mtoPorcParticipacion': reg['mtoPorcParticipacion'],
					'mtoValorFobDolar': reg['mtoValorFobDolar'],
				}
				if 'documentoMod' in reg.keys():
					for mod in reg['documentoMod']:
						values['fecEmisionMod'] = datetime.strptime(mod['fecEmisionMod'], '%d/%m/%Y').date() if 'fecEmisionMod' in mod.keys() else None
						values['codTipoCDPMod'] = mod['codTipoCDPMod']
						values['numSerieCDPMod'] = mod['numSerieCDPMod']
						values['numCDPMod'] = mod['numCDPMod']
				self.env['account.sunat.sire.sale.data'].create(values)
		#return self.env['popup.it'].get_message(arr2)