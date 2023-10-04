from odoo import models, fields, exceptions, api, _
import tempfile
import binascii
import xlrd
from odoo.exceptions import Warning, UserError
import base64


class ImportProductIt(models.TransientModel):
	_name = 'import.product.it'

	file = fields.Binary(string='Archivo')
	import_product_type = fields.Selection([('create','Crear Producto'),('update','Actualizar Producto')],string='Tipo de Operacion', required=True,default="create")
	import_product_search = fields.Selection([('by_code','Por Codigo'),('by_name','Por nombre')],string='Buscar Producto',default="by_code")
	
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
				raise exceptions.Warning(_("Sube un archivo .xlsx!")) 
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

			direccion = self.env['account.main.parameter'].search([('company_id','=',self.env.company.id)],limit=1).dir_create_file

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
			return self.env['popup.it'].get_file('Productos Duplicados.xlsx',base64.encodebytes(b''.join(f.readlines())))

		else:
			return self.env['popup.it'].get_message('NO EXISTEN PRODUCTOS DUPLICADOS.')

	def verify_product(self, values):
		default_code = values.get('default_code')
		product_id = False
		if self.import_product_search == 'by_code':
			product_id = self.env['product.template'].search([('default_code','=', default_code)],limit=1)
		else:
			product_id = self.env['product.template'].search([('name','=', values.get('name'))],limit=1)
		
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
				raise exceptions.Warning(_("Sube un archivo .xlsx!")) 
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
								'categ_id': line[2],
								'type': line[3],
								'barcode': line[4],
								'uom': line[5],
								'po_uom': line[6],
								'sale_price': line[7],
								'cost_price': line[8],
								'weight': line[9],
								'volume': line[10],
								'property_account_income_id': line[11],
								'property_account_expense_id': line[12],
								'sale_ok': line[13],
								'purchase_ok': line[14],
								'is_company': line[15],
								})
					res = self.product_create(values)
				else:
					product_categ_obj = self.env['product.category']
					product_uom_obj = self.env['uom.uom']
					if line[2]=='':
						raise Warning('Campo CATEGORIA no puede estar vacío')
					else:
						categ_id = product_categ_obj.search([('name','=',line[2])])
					if line[3] == 'Consumible':
						type ='consu'
					elif line[3] == 'Servicio':
						type ='service'
					elif line[3] == 'Almacenable':
						type ='product'
					
					if line[5]=='':
						uom_id = 1
					else:
						uom_search_id  = product_uom_obj.search([('name','=',line[5])])
						uom_id = uom_search_id.id
					
					if line[6]=='':
						uom_po_id = 1
					else:
						uom_po_search_id  = product_uom_obj.search([('name','=',line[6])])
						uom_po_id = uom_po_search_id.id
					if line[4] == '':
						barcode = False
					else:
						barcode = line[4]

					income_account_id = None
					expense_account_id = None

					if line[11]:
						income_account_id = self.find_account(line[11])

					if line[12]:
						expense_account_id = self.find_account(line[12])

					sale_ok = False
					purchase_ok = False
					if ((line[13]) == '1'):
						sale_ok = True
						
					if ((line[14]) == '1'):
						purchase_ok = True
						
					if ((line[13]) == 'SI'):
						sale_ok = True
						
					if ((line[14]) == 'SI'):
						purchase_ok = True
					
						
					if self.import_product_search == 'by_code':
						product_ids = self.env['product.template'].search([('default_code','=', line[1])])
						if product_ids:
							product_ids.write({'name':line[0],
												#'default_code': line[1],
												'categ_id': categ_id.id,
												'type': type,
												'barcode': barcode,
												'uom_id': uom_id,
												'uom_po_id': uom_po_id,
												'list_price': line[7],
												'standard_price': line[8],
												'weight': line[9],
												'volume': line[10],
												'sale_ok': sale_ok,
												'purchase_ok': purchase_ok,
												'property_account_income_id':income_account_id,
												'property_account_expense_id': expense_account_id})
						else:
							raise Warning(_('Producto "%s" no encontrado.') % line[1]) 
					else:
						product_ids = self.env['product.template'].search([('name','=', line[0])])
						if product_ids:
							product_ids.write({#'name':line[0],
												'default_code': line[1],
												'categ_id': categ_id.id,
												'type': type,
												'barcode': barcode,
												'uom_id': uom_id,
												'uom_po_id': uom_po_id,
												'list_price': line[7],
												'standard_price': line[8],
												'weight': line[9],
												'volume': line[10],
												'sale_ok': sale_ok,
												'purchase_ok': purchase_ok,
												'property_account_income_id':income_account_id,
												'property_account_expense_id': expense_account_id})
						else:
							raise Warning(_('Producto %s no encontrado.') % line[0])  
	
					
		return self.env['popup.it'].get_message('SE IMPORTARON LOS PRODUCTOS DE MANERA CORRECTA.')
	
	def product_create(self, values):
		product_obj = self.env['product.template']
		product_categ_obj = self.env['product.category']
		product_uom_obj = self.env['uom.uom']
		type = ''
		if values.get('categ_id')=='':
			raise Warning('Campo CATEGORIA no puede estar vacío.')
		else:
			categ_id = product_categ_obj.search([('name','=',values.get('categ_id'))])
			if categ_id :
				categ_id = categ_id
				
			else :
				raise Warning(_('No existe la Categoria %s.') % values.get('categ_id'))  
		
		if values.get('type') == 'Consumible':
			type ='consu'
		elif values.get('type') == 'Servicio':
			type ='service'
		elif values.get('type') == 'Almacenable':
			type ='product'
		else:
			raise Warning(_('%s no es un Tipo de Producto.') % values.get('type'))
		
		if values.get('uom_id')=='':
			uom_id = 1
		else:
			uom_search_id  = product_uom_obj.search([('name','=',values.get('uom'))])
			uom_id = uom_search_id.id
		
		if values.get('uom_po_id')=='':
			uom_po_id = 1
		else:
			uom_po_search_id  = product_uom_obj.search([('name','=',values.get('po_uom'))])
			uom_po_id = uom_po_search_id.id
		if values.get('barcode') == '':
			barcode = False
		else:
			barcode = values.get('barcode')

		income_account_id = None
		expense_account_id = None
		company_id = True if values.get("is_company") == 'SI' else False

		if values.get("property_account_income_id"):
			income_account_id = self.find_account(values.get("property_account_income_id"))

		if values.get("property_account_expense_id"):
			expense_account_id = self.find_account(values.get("property_account_expense_id"))

		sale_ok = False
		purchase_ok = False
		if ((values.get('sale_ok')) == '1'):
			sale_ok = True
			
		if ((values.get('purchase_ok')) == '1'):
			purchase_ok = True
			
		if ((values.get('sale_ok')) == 'SI'):
			sale_ok = True
			
		if ((values.get('purchase_ok')) == 'SI'):
			purchase_ok = True

		vals = {
				'name':values.get('name'),
				'default_code':values.get('default_code'),
				'categ_id':categ_id.id,
				'type':type,
				'barcode':barcode,
				'uom_id':uom_id,
				'uom_po_id':uom_po_id,
				'list_price':values.get('sale_price'),
				'standard_price':values.get('cost_price'),
				'weight':values.get('weight'),
				'volume':values.get('volume'),
				'property_account_income_id': income_account_id,
				'property_account_expense_id': expense_account_id,
				'sale_ok': sale_ok,
				'purchase_ok': purchase_ok,
				'company_id': self.env.company.id if company_id else None,
				}
		res = product_obj.create(vals)
		return res

	def find_account(self, code):
		account_obj = self.env['account.account']
		account_search = account_obj.search([('code', '=', str(code)),('company_id','=',self.env.company.id)],limit=1)
		if account_search:
			return account_search.id
		else:
			raise Warning(_('No existe una Cuenta con el Codigo "%s" en esta Compañia') % code)

	def download_template(self):
		return {
			 'type' : 'ir.actions.act_url',
			 'url': '/web/binary/download_product_import_template',
			 'target': 'new',
			}

