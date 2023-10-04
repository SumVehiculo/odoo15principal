from openerp import models, fields, exceptions, api, _
import tempfile
import binascii
import xlrd
import time
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from datetime import date, datetime
from odoo.exceptions import UserError
from openerp.exceptions import Warning, UserError
import io
import logging
_logger = logging.getLogger(__name__)

try:
	import xlwt
except ImportError:
	_logger.debug('Cannot `import xlwt`.')
try:
	import cStringIO
except ImportError:
	_logger.debug('Cannot `import cStringIO`.')
try:
	import base64
except ImportError:
	_logger.debug('Cannot `import base64`.')
try:
	import csv
except ImportError:
	_logger.debug('Cannot `import csv`.')


class product_pricelist_purchase_import(models.TransientModel):
	_name = "product.pricelist.purchase.import"
	_description = "Importador Tarifas Compra"

	file = fields.Binary(string='Archivo')	
	import_tarifa_type = fields.Selection([('create','Crear Tarifas'),('update','Actualizar Tarifas')],string='Tipo de Operacion', required=True,default="create")
	def verify_if_exists_product(self):
		fp = tempfile.NamedTemporaryFile(delete= False,suffix=".xlsx")
		try :
			fp.write(binascii.a2b_base64(self.file))
			fp.seek(0)
			values = {}
			res = {}
			result = []
			workbook = xlrd.open_workbook(fp.name)
		except Exception:
				raise UserError(_("Sube un archivo .xlsx!")) 
		sheet = workbook.sheet_by_index(0)
		for row_no in range(sheet.nrows):
			val = {}
			if row_no <= 0:
				fields = map(lambda row:row.value.encode('utf-8'), sheet.row(row_no))
			else:
				line = list(map(lambda row:isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
				values.update( {'default_code': line[0],
							})
				gg = self.verify_product(values)
				if gg:
					result.append(gg)

		if len(result)>0:
			import io
			from xlsxwriter.workbook import Workbook
			ReportBase = self.env['report.base']

			direccion = self.env['main.parameter'].search([('company_id','=',self.env.company.id)],limit=1).dir_create_file

			if not direccion:
				raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

			workbook = Workbook(direccion +'Productos_Existentes.xlsx')
			workbook, formats = ReportBase.get_formats(workbook)

			import importlib
			import sys
			importlib.reload(sys)

			worksheet = workbook.add_worksheet("Productos")
			worksheet.set_tab_color('blue')

			HEADERS = ['REFERENCIA INTERNA']
			worksheet = ReportBase.get_headers(worksheet,HEADERS,0,0,formats['boldbord'])
			x=1

			for line in result:
				worksheet.write(x,0,line[0] if line[0] else '',formats['especial1'])				
				x += 1

			widths = [100,19]
			worksheet = ReportBase.resize_cells(worksheet,widths)
			workbook.close()

			f = open(direccion +'Productos_Existentes.xlsx', 'rb')
			return self.env['popup.it'].get_file('Productos Duplicados.xlsx',base64.encodestring(b''.join(f.readlines())))
		else:			
			return self.env['popup.it'].get_message('NO EXISTEN PRODUCTOS DUPLICADOS.')

	def verify_product(self, values):
		s = str(values.get('default_code')).strip()
		default_code = s.rstrip('0').rstrip('.') if '.' in s else s
		product_id = False		
		product_id = self.env['product.template'].search([('default_code','=', default_code)],limit=1)
		
		if product_id:
			return [default_code]

	def tarifa_import(self):              
		fp = tempfile.NamedTemporaryFile(delete= False,suffix=".xlsx")
		try :
			fp.write(binascii.a2b_base64(self.file))
			fp.seek(0)
			values = {}
			res = {}
			workbook = xlrd.open_workbook(fp.name)
		except Exception:
			raise UserError(_("Sube un archivo .xlsx!")) 
		sheet = workbook.sheet_by_index(0)
		for row_no in range(sheet.nrows):
			val = {}
			if row_no <= 0:
				fields = map(lambda row:row.value.encode('utf-8'), sheet.row(row_no))
			else:
				line = list(map(lambda row:isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
				if self.import_tarifa_type == 'create':
					values.update( {'partner':line[0],
								'sku': line[1],
								'price': line[2],								
								'moneda': line[3],
								})
					res = self.product_create(values)
				else:					
					if line[0].strip() == '':
						raise UserError('Campo PROVEEDOR No Puede Estar Vacia')
					if line[1].strip() == '':
						raise UserError('Campo Referencia Interna no puede estar vacío')
					if line[2].strip() == '':
						raise UserError('Campo Precio Unitario no puede estar vacío')
					if line[3].strip() == '':
						raise UserError('Campo Moneda no puede estar vacío')			

					proveedor = self.env['res.partner'].sudo().search([('name', '=', line[0].strip()), '|', ('company_id', '=', self.env.company.id), ('company_id', '=', False)])
					if proveedor:
						if len(proveedor)>1:
							raise UserError("Dos Proveedores Con El Mismo Nombre: "+str(line[0]))
						else:
							producto = self.env['product.product'].sudo().search([('default_code', '=', line[1].strip()), '|', ('company_id', '=', self.env.company.id), ('company_id', '=', False)])
							if producto:
								if len(producto)>1:
									raise UserError("Dos Variantes De Productos con La Misma Referencia Interna: " + str(line[1]))
								else:
									if producto.product_tmpl_id.id:
										moneda = self.env['res.currency'].sudo().search([('name', '=', line[3].strip())])
										if moneda:
											tarifa_compra = self.env['product.supplierinfo'].sudo().search([('name', '=', proveedor.id), ('company_id', '=', self.env.company.id), ('product_tmpl_id', '=', producto.product_tmpl_id.id), ('product_id', '=', producto.id), ('currency_id', '=', moneda.id)])
											if tarifa_compra:
												if len(tarifa_compra)>1:
													raise UserError('Dos Tarifas A Actualizar Encontradas: ' + str(producto.default_code) + " Del Proveedor: " + str(proveedor.name)+ " Con La Moneda: " + str(moneda.name))
												else:
													final = line[2].strip()
													if final[0] == "'":
														final = final[1:]
													if final[-1] == "'":
														final = final[:1]            
													tarifa_compra.sudo().write({'price':float(final)})
											else:
												raise UserError('Tarifa A Actualizar No Encontrada: ' + str(producto.default_code) + " Del Proveedor: " + str(proveedor.name) + " Con La Moneda: " + str(moneda.name))
										else:
											raise UserError('Moneda No Encontrada: ' + str(line[3]))
									else:
										raise UserError('Producto Original no Encontrado De la Variante: ' + str(line[1]))
							else:
								raise UserError('Variante De Producto no Encontrado: ' + str(line[1]))
					else:
						raise UserError("Proveedor No Encontrado: "+str(line[0]))
		return self.env['popup.it'].get_message('SE IMPORTARON LAS TARIFAS DE MANERA CORRECTA.')
	
	def product_create(self, values):
		line_tarif = self.env['product.supplierinfo']

		if values.get('partner').strip() == '':
			raise UserError('Campo Proveedor no puede estar vacío')			
		if values.get('sku').strip() == '':
			raise UserError('Campo REFERENCIA INTERNA no puede estar vacío')
		if values.get('moneda').strip() == '':
			raise UserError('Campo Moneda no puede estar vacío')
		if values.get('price').strip() == '':
			raise UserError('Campo Precio Unitario no puede estar vacío')	

		proveedor = self.env['res.partner'].sudo().search([('name', '=', values.get('partner').strip()), '|', ('company_id', '=', self.env.company.id), ('company_id', '=', False)])
		if proveedor:
			if len(proveedor)>1:
				raise UserError("Dos Proveedores Con El Mismo Nombre: "+str(values.get('partner')))
			else:
				producto = self.env['product.product'].sudo().search([('default_code', '=', values.get('sku').strip()), '|', ('company_id', '=', self.env.company.id), ('company_id', '=', False)])
				if producto:
					if len(producto)>1:
						raise UserError("Dos Variantes De Productos con La Misma Referencia Interna: " + str(values.get('sku')))
					else:
						if producto.product_tmpl_id.id:
							moneda = self.env['res.currency'].sudo().search([('name', '=', values.get('moneda').strip())])
							if moneda:												   
								final = values.get('price').strip()
								if final[0] == "'":
									final = final[1:]
								if final[-1] == "'":
									final = final[:1]
							else:
								raise UserError("Moneda No Encontrada: " + str(values.get('moneda')))
						else:
							raise UserError("Producto Original No Encontrado De La Variante: " + str(values.get('sku')))
				else:
					raise UserError("Variante De Producto No Encontrado: " + str(values.get('sku')))          
		else:
			raise UserError("Proveedor Con Nombre: " + str(values.get('partner')))

		tarifa_compra_repetido = self.env['product.supplierinfo'].sudo().search([('name', '=', proveedor.id), ('company_id', '=', self.env.company.id), ('product_tmpl_id', '=', producto.product_tmpl_id.id), ('product_id', '=', producto.id), ('currency_id', '=', moneda.id)])
		if tarifa_compra_repetido:
			return
		vals = {
			'name': proveedor.id,
            'product_tmpl_id': producto.product_tmpl_id.id,
			'product_id': producto.id,
			'price': float(final),
			'currency_id': moneda.id,
			'company_id': self.env.company.id
				}
		
		res = line_tarif.sudo().create(vals)
		return res	

	def download_template(self):
		return {
			 'type' : 'ir.actions.act_url',
			 'url': '/web/binary/tarifa_purchase_import_template',
			 'target': 'new',
			}
