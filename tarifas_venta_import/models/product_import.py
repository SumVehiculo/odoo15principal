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


class product_pricelist_sale_import(models.TransientModel):
	_name = "product.pricelist.sale.import"
	_description = "Importador Tarifas Venta"

	file = fields.Binary(string='Archivo')
	create_not_found = fields.Boolean("Si No Existe La Tarifa De El Producto a actualizar, Se Creara:")	
	nombre_tarifa = fields.Many2one('product.pricelist',string="Tarifa")
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
					values.update( {'sku':line[0],
								'fixed_price': line[1],
								})
					res = self.product_create(values)
				else:
					tarif = self.nombre_tarifa
					if tarif.id == False:
						raise UserError('Debe Escoger Una Tarifa')
					else:
						if line[0].strip()=='':
							raise UserError('Campo REFERENCIA INTERNA no puede estar vacío')
						if line[1].strip() == '':
							raise UserError('Campo PRECIO FIJO no puede estar vacío')
						producto = self.env['product.product'].sudo().search([('default_code', '=', line[0].strip()), '|', ('company_id', '=', self.env.company.id), ('company_id', '=', False)])
						if producto:
							if len(producto)>1:
								raise UserError("Dos Productos con La Misma Referencia Interna: " + str(line[0]))							
							else:
								line_tarif = self.env['product.pricelist.item'].sudo().search([('company_id', '=', tarif.company_id.id),('product_id', '=', producto.id), ('pricelist_id', '=', tarif.id),('applied_on', '=', '0_product_variant')])
								if len(line_tarif)>1:
									raise UserError('Dos Tarifas Con El Mismo Producto Encontradas: ' + str(producto.default_code))
								if len(line_tarif)<=0:									
									raise UserError('Tarifas Para El Producto No Encontrada: ' + str(producto.default_code))
								if len(line_tarif)==1:
									final = line[1].strip()
									if final[0] == "'":
										final = final[1:]
									if final[-1] == "'":
										final = final[:1]            
									line_tarif.sudo().write({'fixed_price':float(final)})
						else:
							raise UserError('Producto no Encontrado: ' + str(line[0]))
		return self.env['popup.it'].get_message('SE IMPORTARON LAS TARIFAS DE MANERA CORRECTA.')
	
	def product_create(self, values):
		line_tarif = self.env['product.pricelist.item']
		if values.get('sku').strip() == '':
			raise UserError('Campo REFERENCIA INTERNA no puede estar vacío')			
		if values.get('fixed_price').strip() == '':
			raise UserError('Campo PRECIO FIJO no puede estar vacío')
		tarif = self.nombre_tarifa
		if tarif.id == False:
			raise UserError('Debe Escoger Una Tarifa')
		producto = self.env['product.product'].sudo().search([('default_code', '=', values.get('sku').strip()), '|', ('company_id', '=', self.env.company.id), ('company_id', '=', False)])
		if producto:
			if len(producto)>1:
				raise UserError("Dos Productos con La Misma Referencia Interna: " + str(values.get('sku')))
		else:
			raise UserError('Producto no Encontrado: ' + str(values.get('sku')))
			
   
		final = values.get('fixed_price').strip()
		if final[0] == "'":
			final = final[1:]
		if final[-1] == "'":
			final = final[:1]
		line_tarif_repetida = self.env['product.pricelist.item'].sudo().search([('pricelist_id', '=', tarif.id), ('company_id', '=', tarif.company_id.id),('applied_on', '=', '0_product_variant'),('product_id', '=', producto.id)])
		if line_tarif_repetida:
			if len(line_tarif_repetida)>1:
				raise UserError('Dos Tarifas Encontradas Para El Porudcto: ' + str(producto.name))
			else:
				line_tarif_repetida.sudo().write({'fixed_price':float(final)})
		else:
			vals = {
      				'pricelist_id': tarif.id,
					'applied_on': '0_product_variant',      
					'product_id': producto.id,
					'company_id': tarif.company_id.id,
					'compute_price': 'fixed',
					'currency_id': tarif.currency_id.id,
					'fixed_price': float(final)
								  }
		
			res = line_tarif.create(vals)
			return res

	def download_template(self):
		return {
			 'type' : 'ir.actions.act_url',
			 'url': '/web/binary/download_tarifa_sale_import_template',
			 'target': 'new',
			}
