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


class ProductImport(models.TransientModel):
	_name = "product.import"
	_description = "Importador Productos"

	file = fields.Binary(string='Archivo')
	import_product_type = fields.Selection([('create','Crear Producto'),('update','Actualizar Producto')],string='Tipo de Operacion', required=True,default="create")
	import_product_search = fields.Selection([('by_code','Por Codigo'),('by_name','Por nombre')],string='Buscar Producto',default="by_code")
	create_categ = fields.Boolean(string="Si No Existe La Categoria, Se Creara:", default=False)
	
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
				values.update( {'name':line[0],
							'default_code': line[1],
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

			HEADERS = ['NOMBRE','REFERENCIA INTERNA']
			worksheet = ReportBase.get_headers(worksheet,HEADERS,0,0,formats['boldbord'])
			x=1

			for line in result:
				worksheet.write(x,0,line[0] if line[0] else '',formats['especial1'])
				worksheet.write(x,1,line[1] if line[1] else '',formats['especial1'])
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
		if self.import_product_search == 'by_code':
			product_id = self.env['product.template'].search([('default_code','=', default_code)],limit=1)
		else:
			product_id = self.env['product.template'].search([('name','=', values.get('name').strip())],limit=1)
		
		if product_id:
			return [values.get('name'),default_code]

	def product_import(self):              
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
				if self.import_product_type == 'create':
					values.update( {'name':line[0],
								'default_code': line[1],
								'uom': line[2],
								'po_uom': line[3],
        						'purchase_ok': line[4],
								'sale_ok': line[5],
        						'type': line[6],
              					'invoice_policy':line[7],
								'taxes_id':line[8],
								'supplier_taxes_id':line[9],
								'categ_id': line[10],
								'purchase_method': line[11],
								'route_ids': line[12],
								'tracking':line[13],
								'property_account_income_id': line[14],
								'property_account_expense_id': line[15],
								'sale_price': line[16],
        						'cost_price': line[17],
								'barcode': line[18],
								'weight': line[19],
								'volume': line[20],
								'is_company': line[21],
								'description_sale':line[22],
        						'product_brand_id':line[23],
								})
					res = self.product_create(values)
				else:
					product_categ_obj = self.env['product.category']
					product_uom_obj = self.env['uom.uom']
					if line[7].strip()=='':
						raise UserError('Campo Politica de Facturación no puede estar vacío')
					else:
						if ((line[7]).strip().lower() == 'cantidades entregadas'):
							politica_facturacion = 'delivery'
						elif ((line[7]).strip().lower() == 'cantidades pedidas'):
							politica_facturacion = 'order'
						else:
							raise UserError("Campo Politica de Facturación Solo Puede LLenarse con Los Campos Del Formato Descargable, usted ingresaso:" + str((line[7]).strip()))
   
					if line[11].strip()=='':
						raise UserError('Campo Politica de Control no puede estar vacío')
					else:
						if ((line[11]).strip().lower() == 'sobre cantidades pedidas'):
							politica_control = 'purchase'
						elif ((line[11]).strip().lower() == 'sobre cantidades recibidas'):
							politica_control = 'receive'
						else:
							raise UserError("Campo Politica de Control Solo Puede LLenarse con Los Campos Del Formato Descargable ingresaste:" + str((line[11]).strip()))
   
					if line[0].strip()=='':
						raise UserError('Campo NOMBRE no puede estar vacío')
					if line[1].strip()=='':
						raise UserError('Campo REFERENCIA INTERNA/SKU no puede estar vacío')
					if line[6].strip()=='':
						raise UserError('Campo TIPO PRODUCTO no puede estar vacío')
					if line[6].strip() == 'Consumible':
						type ='consu'
					elif line[6].strip() == 'Servicio':
						type ='service'
					elif line[6].strip() == 'Almacenable':
						type ='product'
					else:
						raise UserError('Campo TIPO PRODUCTO no disponible: ' + str(line[6]))
					if line[4].strip()=='':
						raise UserError('Campo Puede Ser Comprado no puede estar vacío')
					else:
						if ((line[4]).strip() == 'VERDADERO'):
							purchase_ok = True
						elif ((line[4]).strip() == 'FALSO'):
							purchase_ok = False
						elif ((line[4]).strip() == '1'):
							purchase_ok = True
						elif ((line[4]).strip() == '0'):
							purchase_ok = False
						else:
							raise UserError("Campo Puede ser comprado Solo Puede LLenarse con 'VERDADERO' o 'FALSO' ingresaste:" + str((line[4]).strip()))
					if line[5].strip()=='':
						raise UserError('Campo Puede Ser Vendido no puede estar vacío')
					else:
						if ((line[5]).strip() == 'VERDADERO'):
							sale_ok = True
						elif ((line[5]).strip() == 'FALSO'):
							sale_ok = False
						elif ((line[5]).strip() == '1'):
							sale_ok = True
						elif ((line[5]).strip() == '0'):
							sale_ok = False
						else:
							raise UserError("Campo Puede ser comprado Solo Puede LLenarse con 'VERDADERO' o 'FALSO' ingresaste:" + str((line[5]).strip()))     
					if line[13].strip()=='' and type!='service':
						raise UserError('Campo SEGUIMIENTO/TRAZABILIDAD no puede estar vacío')
					else:
						if line[13].strip().lower() == 'serial':
							trazabilidad = 'serial'							
						elif line[13].strip().lower() == 'por numero de serie unico':
							trazabilidad = 'serial'
						elif line[13].strip().lower() == 'por número de serie único':
							trazabilidad = 'serial'						
						elif line[13].strip().lower() == 'por lotes':
							trazabilidad = 'lot'							
						elif line[13].strip().lower() == 'sin seguimiento':
							trazabilidad = 'none'
						elif type=='service':				
							pass
						else:
							raise UserError('Campo TRAZABILIDAD no disponible: ' + str(line[13]))
					if type=='service':
						trazabilidad = 'none'
					if line[10]=='':
						raise UserError('Campo CATEGORIA no puede estar vacío')
					else:
						padre_id = False
						for i in line[10].split('|'):
							categ_id = product_categ_obj.search([('name','=',str(i).strip()),('parent_id','=',padre_id)])
							padre_id = categ_id.id
							if categ_id.id == False:
								raise UserError('Categoria no encontrado: ' + str(i))					
					if line[2]=='':
						uom_id = 1
					else:
						uom_search_id  = product_uom_obj.search([('name','=',line[2].strip())])
						if uom_search_id:
							if len(uom_search_id)>1:
								raise UserError('Dos Unidad De Medida disponible con el mismo nombre: ' + str(line[2]))
							uom_id = uom_search_id.id
						else:
							raise UserError('Unidad De Medida no disponible: ' + str(line[2]))
					if line[3]=='':
						uom_po_id = 1
					else:
						uom_po_search_id  = product_uom_obj.search([('name','=',line[3].strip())])
						if uom_po_search_id:
							if len(uom_po_search_id)>1:
								raise UserError('Dos Unidad De Medida disponible con el mismo nombre: ' + str(line[3]))
							uom_po_id = uom_po_search_id.id
						else:
							raise UserError('Unidad De Medida no disponible: ' + str(line[3]))
					if line[18] == '':
						barcode = False
					else:
						barcode = line[18].strip()
					income_account_id = None
					expense_account_id = None
					marca = False
					if line[23].strip()!='':
						marca_s = self.env['product.brand'].sudo().search([('name','=', line[23].strip())])
						if marca_s:
							if len(marca_s)>1:
								raise UserError("Dos Marcas Con Mismo Nombre: " + line[23].strip())
							marca = marca_s.id
						else:
							raise UserError("Marca No Encontrada: " + line[23].strip())
					if line[14]:
						s = str(line[14]).strip()
						account_in = s.rstrip('0').rstrip('.') if '.' in s else s
						income_account_id = self.find_account(account_in)

					if line[15]:
						s = str(line[15]).strip()
						account_ex = s.rstrip('0').rstrip('.') if '.' in s else s
						expense_account_id = self.find_account(account_ex)

					ids_impuestos_clientes = []
					if line[8]:
						for i in line[8].split('|'):
							tax_cliente = self.env['account.tax'].sudo().search([('name','=',str(i).strip()),('type_tax_use','=','sale')])
							if tax_cliente:
								if len(tax_cliente)>1:
									raise UserError('Dos Impuesto De Cliente Encontrado Con Nombre: ' + str(i))
								else:
									if tax_cliente.id in ids_impuestos_clientes:
										pass
									else:
										ids_impuestos_clientes.append(tax_cliente.id)
							else:
								raise UserError('Impuesto De Cliente No Encontrado: ' + str(i))
					ids_impuestos_proveedor = []
					if line[9]:
						for i in line[9].split('|'):
							tax = self.env['account.tax'].sudo().search([('name','=',str(i).strip()),('type_tax_use','=','purchase')])
							if tax:
								if len(tax)>1:
									raise UserError('Dos Impuesto De Proveedor Encontrado Con Nombre: ' + str(i))
								else:
									if tax.id in ids_impuestos_proveedor:
										pass
									else:
										ids_impuestos_proveedor.append(tax.id)
							else:
								raise UserError('Impuesto De Proveedor No Encontrado: ' + str(i))
					ids_rutas = []
					if line[12]:
						if type =='service':
							raise UserError('Producto No Pude Tener Ruta Si Es Tipo Servicio: ' + str(line[1]))
						for i in line[12].split('|'):
							ruta = self.env['stock.location.route'].sudo().search([('name','=',str(i).strip()),('product_selectable','=',True)])
							if ruta:
								if len(ruta)>1:
									raise UserError('Dos Rutas Con mismo Nombre: ' + str(i))
								else:
									if ruta.id in ids_rutas:
										pass
									else:
										ids_rutas.append(ruta.id)
							else:
								raise UserError('Ruta No Encontrada: ' + str(i))
					if self.import_product_search == 'by_code':
						product_ids = self.env['product.template'].search([('default_code','=', line[1].strip()),'|', ('company_id', '=', self.env.company.id), ('company_id', '=', False)])
						if product_ids:
							if len(product_ids)>1:
								raise UserError(_('Dos Productos "%s" Con la misma Referencia Interna.') % line[1]) 
							product_ids.write({'name':line[0].strip(),
												#'default_code': line[1],
												'uom_id': uom_id,
            									'uom_po_id': uom_po_id,
												'purchase_ok': purchase_ok,
												'sale_ok': sale_ok,
												'type': type,
            									'invoice_policy':politica_facturacion,
												'taxes_id':[(6, 0, [(n)for n in ids_impuestos_clientes])],
												'supplier_taxes_id':[(6, 0, [(m)for m in ids_impuestos_proveedor])],            
												'categ_id': categ_id.id,
												'purchase_method':politica_control,
            									'tracking':trazabilidad,
                     							'property_account_income_id':income_account_id,
												'property_account_expense_id': expense_account_id,
 												'list_price': line[16],
             									'standard_price': line[17],
												'barcode': barcode,
												'weight': line[19],
												'volume': line[20],
												'description_sale': line[22].strip() if line[22].strip()!='' else False,
            									})
							product_ids.refresh()
							if len(ids_rutas)>1:
								if product_ids.has_available_route_ids == False or product_ids.type=='service':
									raise UserError("No Puede Ingresar Rutas A Un Producto Tipo Servicio: " +str(line[1]))
								else:
									product_ids.write({
             						'route_ids':[(6, 0, [(z)for z in ids_rutas])]
                            })
							else:
								product_ids.write({
             						'route_ids':[(6, 0, [(z)for z in ids_rutas])]
									})
							if line[23].strip()!='':
								product_ids.write({'product_brand_id':marca})
						else:
							raise UserError(_('Producto "%s" no encontrado.') % line[1]) 
					else:
						product_ids = self.env['product.template'].search([('name','=', line[0].strip()),'|', ('company_id', '=', self.env.company.id), ('company_id', '=', False)])
						if product_ids:
							if len(product_ids)>1:
								raise UserError(_('Dos Productos "%s" Con el mismo Nombre.') % line[0]) 
							product_ids.write({#'name':line[0],
												'default_code': line[1].strip(),
												'uom_id': uom_id,
            									'uom_po_id': uom_po_id,
												'purchase_ok': purchase_ok,
												'sale_ok': sale_ok,
												'type': type,
            									'invoice_policy':politica_facturacion,
												'taxes_id':[(6, 0, [(n)for n in ids_impuestos_clientes])],
												'supplier_taxes_id':[(6, 0, [(m)for m in ids_impuestos_proveedor])],            
												'categ_id': categ_id.id,
												'purchase_method':politica_control,
            									'tracking':trazabilidad,
                     							'property_account_income_id':income_account_id,
												'property_account_expense_id': expense_account_id,
 												'list_price': line[16],
             									'standard_price': line[17],
												'barcode': barcode,
												'weight': line[19],
												'volume': line[20],
												'description_sale': line[22].strip() if line[22].strip()!='' else False,
            									})
							product_ids.refresh()
							if len(ids_rutas)>1:
								if product_ids.has_available_route_ids == False or product_ids.type=='service':
									raise UserError("No Puede Ingresar Rutas A Un Producto Tipo Servicio: " +str(line[1]))
								else:
									product_ids.write({
             						'route_ids':[(6, 0, [(z)for z in ids_rutas])]
                            		})
							else:
								product_ids.write({
             						'route_ids':[(6, 0, [(z)for z in ids_rutas])]
									})
							if line[23].strip()!='':
								product_ids.write({'product_brand_id':marca})
						else:
							raise UserError(_('Producto %s no encontrado.') % line[0])
		return self.env['popup.it'].get_message('SE IMPORTARON LOS PRODUCTOS DE MANERA CORRECTA.')
	
	def product_create(self, values):
		product_obj = self.env['product.template']
		product_categ_obj = self.env['product.category']
		product_uom_obj = self.env['uom.uom']
		if values.get('name').strip()=='':
			raise UserError('Campo NOMBRE no puede estar vacío.')
		if values.get('default_code').strip()=='':
			raise UserError('Campo REFERENCIA INTERNA/SKU no puede estar vacío.')
		product_repetido = self.env['product.template'].sudo().search([('default_code','=', values.get('default_code').strip()),'|', ('company_id', '=', self.env.company.id), ('company_id', '=', False)])
		if product_repetido:
			return
		if values.get('invoice_policy').strip()=='':
			raise UserError('Campo Politica de Facturación no puede estar vacío')
		else:
			if ((values.get('invoice_policy')).strip() == 'Cantidades entregadas'):
				politica_facturacion = 'delivery'
			elif ((values.get('invoice_policy')).strip() == 'Cantidades pedidas'):
				politica_facturacion = 'order'
			else:
				raise UserError("Campo Politica de Facturación Solo Puede LLenarse con Los Campos Del Formato Descargable, usted ingresaso:" + str(values.get('invoice_policy').strip()))
		if values.get('purchase_method').strip()=='':
			raise UserError('Campo Politica de Control no puede estar vacío')
		else:
			if ((values.get('purchase_method')).strip() == 'Sobre cantidades pedidas'):
				politica_control = 'purchase'
			elif ((values.get('purchase_method')).strip() == 'Sobre cantidades recibidas'):
				politica_control = 'receive'
			else:
				raise UserError("Campo Politica de Facturación Solo Puede LLenarse con Los Campos Del Formato Descargable, usted ingresaso:" + str(values.get('purchase_method').strip()))
		type = ''
		if values.get('type').strip()=='':
			raise UserError('Campo TIPO PRODUCTO no puede estar vacío.')
		if values.get('type') == 'Consumible':
			type ='consu'
		elif values.get('type') == 'Servicio':
			type ='service'
		elif values.get('type') == 'Almacenable':
			type ='product'
		else:
			raise UserError(_('%s no es un Tipo de Producto.') % values.get('type'))
		if values.get('tracking').strip()=='' and type!='service':
			raise UserError('Campo Seguimiento/TRAZABILIDAD no puede estar vacío.')
		else:
			if values.get('tracking').strip().lower() == 'serial':
				trazabilidad = 'serial'
			elif values.get('tracking').strip().lower() == 'por numero de serie unico':
				trazabilidad = 'serial'
			elif values.get('tracking').strip().lower() == 'por número de serie único':
				trazabilidad = 'serial'
			elif values.get('tracking').strip().lower() == 'por lotes':
				trazabilidad = 'lot'
			elif values.get('tracking').strip().lower() == 'sin seguimiento':
				trazabilidad = 'none'
			elif type=='service':				
				pass
			else:
				raise UserError('Campo TRAZABILIDAD no disponible: ' + str(values.get('tracking')))
		if type=='service':
			trazabilidad = 'none'
		
		
		if values.get('uom_id')=='':
			uom_id = 1
		else:
			uom_search_id  = product_uom_obj.search([('name','=',values.get('uom').strip())])
			if uom_search_id:
				if len(uom_search_id)>1:
					raise UserError('Dos Unidad De Medida disponible con el mismo nombre: ' + str(values.get('uom')))
				uom_id = uom_search_id.id
			else:
				raise UserError('Unidad De Medida no disponible: ' + str(values.get('uom')))
		
		if values.get('uom_po_id')=='':
			uom_po_id = 1
		else:
			uom_po_search_id  = product_uom_obj.search([('name','=',values.get('po_uom').strip())])
			if uom_po_search_id:
				if len(uom_po_search_id)>1:
					raise UserError('Dos Unidad De Medida disponible con el mismo nombre: ' + str(values.get('po_uom')))
				uom_po_id = uom_po_search_id.id
			else:
				raise UserError('Unidad De Medida no disponible: ' + str(values.get('po_uom')))

		if values.get('barcode') == '':
			barcode = False
		else:
			barcode = values.get('barcode').strip()

		income_account_id = None
		expense_account_id = None
		company_id = True if values.get("is_company").strip() == 'SI' else False

		if values.get("property_account_income_id"):
			s = str(values.get("property_account_income_id")).strip()
			account_in = s.rstrip('0').rstrip('.') if '.' in s else s
			income_account_id = self.find_account(account_in)

		if values.get("property_account_expense_id"):
			s = str(values.get("property_account_expense_id")).strip()
			account_ex = s.rstrip('0').rstrip('.') if '.' in s else s
			expense_account_id = self.find_account(account_ex)
		
		if values.get('purchase_ok').strip()=='':
			raise UserError('Campo Puede Ser Comprado no puede estar vacío')
		else:
			if ((values.get('purchase_ok')).strip() == 'VERDADERO'):
				purchase_ok = True
			elif ((values.get('purchase_ok')).strip() == 'FALSO'):
				purchase_ok = False
			elif ((values.get('purchase_ok')).strip() == '1'):
				purchase_ok = True
			elif ((values.get('purchase_ok')).strip() == '0'):
				purchase_ok = False
			else:
				raise UserError("Campo Puede ser comprado Solo Puede LLenarse con 'VERDADERO' o 'FALSO' ingresaste:" + str((values.get('purchase_ok')).strip()))

		if values.get('sale_ok').strip()=='':
			raise UserError('Campo Puede Ser Vendido no puede estar vacío')
		else:
			if ((values.get('sale_ok')).strip() == 'VERDADERO'):
				sale_ok = True
			elif ((values.get('sale_ok')).strip() == 'FALSO'):
				sale_ok = False
			elif ((values.get('sale_ok')).strip() == '1'):
				sale_ok = True
			elif ((values.get('sale_ok')).strip() == '0'):
				sale_ok = False
			else:
				raise UserError("Campo Puede ser comprado Solo Puede LLenarse con 'VERDADERO' o 'FALSO' ingresaste:" + str((values.get('sale_ok')).strip()))
		if values.get('categ_id')=='':
			raise UserError('Campo CATEGORIA no puede estar vacío.')
		else:
			categ = values.get('categ_id').strip()
			padre_id = False
			for i in categ.split('|'):				
				categ_id = product_categ_obj.search([('name','=',str(i).strip()),('parent_id','=',padre_id)])
				padre_id = categ_id.id
				if categ_id.id == False:										
					raise UserError('Categoria no encontrado: ' + str(i))

		marca = False
		if values.get("product_brand_id").strip() != '':
			marca_s = self.env['product.brand'].sudo().search([('name','=', values.get('product_brand_id').strip())])
			if marca_s:
				if len(marca_s)>1:
					raise UserError("Dos Marcas Con Mismo Nombre: " + values.get('product_brand_id').strip())
				marca = marca_s.id
			else:
				raise UserError(_('%s , Marca No Encontrada.') % values.get('product_brand_id'))
		ids_impuestos_clientes = []  
		if values.get("taxes_id"):
			for i in values.get("taxes_id").split('|'):
				tax_cliente = self.env['account.tax'].sudo().search([('name','=',str(i).strip()),('type_tax_use','=','sale')])
				if tax_cliente:
					if len(tax_cliente)>1:
						raise UserError('Dos Impuesto De Cliente Encontrado Con Nombre: ' + str(i))
					else:
						if tax_cliente.id in ids_impuestos_clientes:
							pass
						else:
							ids_impuestos_clientes.append(tax_cliente.id)
				else:
					raise UserError('Impuesto De Cliente No Encontrado: ' + str(i))
		ids_impuestos_proveedor = []
		if values.get("supplier_taxes_id"):
			for i in values.get("supplier_taxes_id").split('|'):
				tax = self.env['account.tax'].sudo().search([('name','=',str(i).strip()),('type_tax_use','=','purchase')])
				if tax:
					if len(tax)>1:
						raise UserError('Dos Impuesto De Proveedor Encontrado Con Nombre: ' + str(i))
					else:
						if tax.id in ids_impuestos_proveedor:
							pass
						else:
							ids_impuestos_proveedor.append(tax.id)
				else:
					raise UserError('Impuesto De Proveedor No Encontrado: ' + str(i))
		ids_rutas = []
		if values.get("route_ids"):
			if type =='service':
				raise UserError('Producto No Pude Tener Ruta Si Es Tipo Servicio: ' + str(values.get("default_code")))
			for i in values.get("route_ids").split('|'):
				ruta = self.env['stock.location.route'].sudo().search([('name','=',str(i).strip()),('product_selectable','=',True)])
				if ruta:
					if len(ruta)>1:
						raise UserError('Dos Rutas Con mismo Nombre: ' + str(i))
					else:
						if ruta.id in ids_rutas:
							pass
						else:
							ids_rutas.append(ruta.id)
				else:
					raise UserError('Ruta No Encontrada: ' + str(i))
		vals = {
								'name':values.get('name').strip(),
								'default_code':values.get('default_code').strip(),
        						'uom_id':uom_id,
              					'uom_po_id':uom_po_id,
								'purchase_ok': purchase_ok,
								'sale_ok': sale_ok,
								'type':type,
								'invoice_policy':politica_facturacion,
								'taxes_id':[(6, 0, [(n)for n in ids_impuestos_clientes])],
								'supplier_taxes_id':[(6, 0, [(m)for m in ids_impuestos_proveedor])],
								'categ_id': categ_id.id,
								'purchase_method':politica_control,
								'tracking':trazabilidad,
								'property_account_income_id': income_account_id,
								'property_account_expense_id': expense_account_id,
								'list_price':values.get('sale_price'),
								'standard_price':values.get('cost_price'),																
								'barcode':barcode,
								'weight':values.get('weight'),
								'volume':values.get('volume'),
								'company_id': self.env.company.id if company_id else False,
								'description_sale': values.get('description_sale').strip() if values.get('description_sale').strip() != '' else False,
								}
		if values.get("product_brand_id").strip() != '':
			vals["product_brand_id"] = marca
		res = product_obj.create(vals)
		res.refresh()
		if len(ids_rutas)>1:
			if res.has_available_route_ids == False or res.type=='service':
				raise UserError("No Puede Ingresar Rutas A Un Producto Tipo Servicio: " +str(res.default_code))
			else:
				res.write({
             	'route_ids':[(6, 0, [(z)for z in ids_rutas])]
        		})
		else:
			res.write({
             	'route_ids':[(6, 0, [(z)for z in ids_rutas])]
				})
		return res

	def find_account(self, code):
		account_obj = self.env['account.account']
		account_search = account_obj.search([('code', '=', str(code)),('company_id','=',self.env.company.id)])
		if account_search:
			if len(account_search)>1:
				raise UserError(_('Dos Cuentas Existentes con el Codigo "%s" en esta Compañia') % code)
			else:
				return account_search.id
		else:
			raise UserError(_('No existe una Cuenta con el Codigo "%s" en esta Compañia') % code)

	def download_template(self):
		return {
			 'type' : 'ir.actions.act_url',
			 'url': '/web/binary/download_product_import_template_s',
			 'target': 'new',
			}
