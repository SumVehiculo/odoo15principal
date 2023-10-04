# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

import tempfile
import binascii
import xlrd
from odoo.exceptions import UserError
from odoo.exceptions import Warning, UserError
from odoo import models, fields, exceptions, api, _
import time
from datetime import date, datetime
import io
import logging
_logger = logging.getLogger(__name__)

try:
	import csv
except ImportError:
	_logger.debug('Cannot `import csv`.')
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

class gen_partner_s(models.TransientModel):
	_name = "gen.partner.s"

	file = fields.Binary('Archivo')
	file_name = fields.Char()
	partner_option = fields.Selection([('create','Crear Partner'),('update','Actualizar Partner')],string='Opcion', required=True,default="create")
	
	def find_country(self,val):
		if type(val) == dict:
			country_search = self.env['res.country'].search([('name','=',val.get('country').strip())])
			if country_search:
				return country_search.id
			else:
				raise UserError(u'El país %s no está disponible en el sistema.'%(val.get('country')))
		else:
			country_search = self.env['res.country'].search([('name','=',val[8].strip())])
			if country_search:
				return country_search.id
			else:
				raise UserError(u'El país %s no está disponible en el sistema.'%(val[8]))
	
	def find_state(self,val):
		if type(val) == dict:
			state_search = self.env['res.country.state'].search([('name','=',val.get('state').strip())])
			if state_search:
				return state_search.id
			else:
				raise UserError(u'El estado %s no está disponible en el sistema.'%(val.get('state')))
		else:
			state_search = self.env['res.country.state'].search([('name','=',val[6].strip())])
			if state_search:
				return state_search.id
			else:
				raise UserError(u'El estado %s no está disponible en el sistema.'%(val[6]))

	def create_partner(self, values):
		parent = state = country = l10n_latam = saleperson =  vendor_pmt_term = cust_pmt_term = False
		if values.get('name').strip() == '':
			raise UserError(_('El campo "Nombre" no puede estar vacio.'))
		if values.get('tipo_direccion'):
			if ((values.get('tipo_direccion')).strip() == 'contact'):
				tipo_contacto = 'contact'
			elif ((values.get('tipo_direccion')).strip() == 'invoice'):
				tipo_contacto = 'invoice'
			elif ((values.get('tipo_direccion')).strip() == 'delivery'):
				tipo_contacto = 'delivery'
			elif ((values.get('tipo_direccion')).strip() == 'other'):
				tipo_contacto = 'other'
			elif ((values.get('tipo_direccion')).strip() == 'private'):
				tipo_contacto = 'private'
			else:
				raise UserError("Tipo de Dirección no Disponible: "+values.get('tipo_direccion'))
		else:
			raise UserError("El Campo Tipo de Dirección no puede estar vacio")

		if values.get('state'):
			state = self.find_state(values)
		if values.get('country'):
			country = self.find_country(values)
		
  
		if values.get('company_id').strip()== '':
			raise UserError('Campo COMPAÑIA Obligatorio.')
		else:
			if ((values.get('company_id')).strip() == '1'):
				company_id_v = self.env.company.id
			elif ((values.get('company_id')).strip().lower() == 'verdadero'):
				company_id_v = self.env.company.id
			elif ((values.get('company_id')).strip().lower() == 'falso'):
				company_id_v = False
			elif ((values.get('company_id')).strip() == '0'):
				company_id_v = False
			else:
				raise UserError('Campo COMPAÑIA No Disponible segun formato, usted ingreso: ' + str(values.get('company_id')).strip())
		
  
  
		if str(values.get('is_not_home')).strip()== '':
			raise UserError('Campo NO DOMICILIADO es Obligatorio')
		else:
			if ((values.get('is_not_home')).strip() == '1'):
				is_not_home_v = True
			elif ((values.get('is_not_home')).strip().lower() == 'verdadero'):
				is_not_home_v = True
			elif ((values.get('is_not_home')).strip().lower() == 'falso'):
				is_not_home_v = False
			elif ((values.get('is_not_home')).strip() == '0'):
				is_not_home_v = False
			else:
				raise UserError('Campo NO DOMICILIADO No Disponible segun formato, usted ingreso: ' + str(values.get('is_not_home')).strip())

		phone_v = False
		if values.get('phone').strip() != '':
			s = str(values.get('phone')).strip()
			phone_v = s.rstrip('0').rstrip('.') if '.' in s else s
		mobile_v = False
		if values.get('mobile').strip() != '':
			s = str(values.get('mobile')).strip()
			mobile_v = s.rstrip('0').rstrip('.') if '.' in s else s
		moneda = False
		if values.get('moneda').strip() != '':
			if values.get('moneda').strip() == "USD" or values.get('moneda').strip() == "USD (USD)":
				moneda_id = self.env['res.currency'].search([('name','=','USD')])
			elif values.get('moneda').strip() == "PEN" or values.get('moneda').strip() == "PEN (PEN)":
				moneda_id = self.env['res.currency'].search([('name','=','PEN')])
			else:
				raise UserError('*Recuerde que solo estan disponibles dolares y soles. Campo Moneda Del Credito No Disponible segun formato, usted ingreso: ' + str(values.get('moneda')).strip())
			moneda = moneda_id.id
  
		
		
		if values.get('saleperson'):
			saleperson_search = self.env['res.users'].search([('name','=',values.get('saleperson').strip())])
			if not saleperson_search:
				raise UserError(_('"%s" Usuario no Disponible en el Sistema.') % values.get('saleperson'))
			else:
				saleperson = saleperson_search.id
		if values.get('cust_pmt_term'):
			cust_payment_term_search = self.env['account.payment.term'].search([('name','=',values.get('cust_pmt_term').strip())])
			if cust_payment_term_search:
				cust_pmt_term = cust_payment_term_search.id
			else:       
				raise UserError(_('"%s" Termino de Pago Cliente no encontrado en su sistema.') % values.get('cust_pmt_term'))
		if values.get('vendor_pmt_term'):
			vendor_payment_term_search = self.env['account.payment.term'].search([('name','=',values.get('vendor_pmt_term').strip())])			
			if vendor_payment_term_search:
				vendor_pmt_term = vendor_payment_term_search.id
			else:       
				raise UserError(_('"%s" Termino de Pago Proveedor no encontrado en su sistema.') % values.get('vendor_pmt_term'))
		
		if ((values.get('customer')).strip() == ''):
			raise UserError('El Campo Cliente no Puede estar Vacio')
		else:
			if ((values.get('customer')).strip() == '1'):
				is_customer = True			
			elif ((values.get('customer')).strip().lower() == 'verdadero'):
				is_customer = True
			elif ((values.get('customer')).strip().lower() == 'falso'):
				is_customer = False
			elif ((values.get('customer')).strip() == '0'):
				is_customer = False
			else:
				raise UserError('Campo Cliente No Disponible segun formato, usted ingreso: ' + str(values.get('customer')).strip())
			
		if ((values.get('vendor')).strip() == ''):
			raise UserError('El Campo Proveedor no Puede estar Vacio')
		else:
			if ((values.get('vendor')).strip() == '1'):
				is_supplier = True			
			elif ((values.get('vendor')).strip().lower() == 'verdadero'):
				is_supplier = True
			elif ((values.get('vendor')).strip().lower() == 'falso'):
				is_supplier = False
			elif ((values.get('vendor')).strip() == '0'):
				is_supplier = False
			else:
				raise UserError('Campo Proveedor No Disponible segun formato, usted ingreso: ' + str(values.get('vendor')).strip())
		

		

		if str(values.get('partner_id')) == '':
			raise UserError(_('El campo "partner_id" no puede estar vacio.'))

		s = str(values.get("vat")).strip()
		vat = s.rstrip('0').rstrip('.') if '.' in s else s

		s = str(values.get("ref")).strip()
		ref = s.rstrip('0').rstrip('.') if '.' in s else s

		property_account_receivable_id = None
		property_account_payable_id = None

		if values.get("cta_cobrar"):
			s = str(values.get("cta_cobrar")).strip()
			account_in = s.rstrip('0').rstrip('.') if '.' in s else s
			property_account_receivable_id = self.find_account(account_in)

		zip_s = False
		if values.get("zip"):
			s = str(values.get("zip")).strip()
			zip_s = s.rstrip('0').rstrip('.') if '.' in s else s


		titulo = False
		if values.get("cta_pagar"):
			s = str(values.get("cta_pagar")).strip()
			account_ex = s.rstrip('0').rstrip('.') if '.' in s else s
			property_account_payable_id = self.find_account(account_ex)
		
		if values.get('type').strip() != '':
			if values.get('type').strip() == 'company' or values.get('type').strip().lower() == 'compañia' or values.get('type').strip().lower() == 'compañía':
				if tipo_contacto != 'contact':
					raise UserError('No puede Puede crear un contacto tipo compañia y no ser de tipo direccion Contacto: '+str(values.get('name')))
				if values.get('puesto_trabajo'):
					raise UserError('No puede Tener Puesto De Trabajo Si es Contacto tipo Compañia: '+str(values.get('name')))
				if values.get('titulo'):
					raise UserError('No puede Tener Titulo Si es un Contacto Tipo Compañia: '+str(values.get('name')))
				if values.get('parent'):
					raise UserError('No puede dar padre si ha seleccionado el tipo de empresa: ' +str(values.get('name')))
				type =  'company'
			elif values.get('type').strip() == 'person' or values.get('type').strip().lower() == 'individual':
				type =  'person'
				if values.get('titulo'):
					titulo_ids = self.env['res.partner.title'].sudo().search([('name','=',values.get('titulo').strip())])
					if titulo_ids:
						if len(titulo_ids)>1:
							raise UserError('Dos Titulos Con Mismo Nombre: '+str(values.get('titulo')))
						else:
							titulo = titulo_ids.id
					else:
						raise UserError('Titulo no Encontrado: '+str(values.get('titulo')))
				parent = False
				abuelo = False
				if values.get('parent'):
					for i in values.get('parent').split('|'):
						#parent_search = self.env['res.partner'].search([('vat','=',vat),('l10n_latam_identification_type_id','=',l10n_latam),('parent_id','=',abuelo),('name','=',str(i).strip())])
						parent_search = self.env['res.partner'].search([('parent_id','=',abuelo),('name','=',str(i).strip())])
						if parent_search:
							if len(parent_search)>1:
								raise UserError("Dos Contactos Padre Con Mismo Nombre: "+str(i).strip())
							parent =  parent_search.id
							abuelo = parent_search.id
						else:
							raise UserError(' Contactos Padre No Encontrado Con Numero Identificacion: '+str(vat)+" Con Tipo Identificacion con codigo sunat: "+str(values.get('type_document_id')).strip() +" Con Nombre: "+str(i).strip())
			else:
				raise UserError('Tipo de Contacto no Disponible, Usted Ingreso: '+str(values.get('type').strip()))
		else:
			raise UserError('Campo Tipo Contacto No puede estar Vacio')
		if type=='person':
			if parent == False:
				if str(values.get('type_document_id')).strip() == '':
					raise UserError(_('El campo "Tipo De Documento" no puede estar vacio.'))
				else:			
					s = str(values.get("type_document_id"))
					type_document_id = s.rstrip('0').rstrip('.') if '.' in s else s			
					l10n_latam_search = self.env['l10n_latam.identification.type'].search([('code_sunat','=',type_document_id)])
					if not l10n_latam_search:
						raise UserError("Tipo de Doc. no disponible en el sistema Con Codigo Sunat: "+str(type_document_id))
					else:
						if len(l10n_latam_search)>1:
							raise UserError("Dos Tipos de Documentos Con El Mismo Codigo Sunat en el sistema:"+str(type_document_id))
						else:
							l10n_latam = l10n_latam_search.id
			else:
				padre_obj = self.env['res.partner'].search([('id','=',parent)])
				l10n_latam = padre_obj.l10n_latam_identification_type_id.id
		else:
			if str(values.get('type_document_id')).strip() == '':
				raise UserError(_('El campo "Tipo De Documento" no puede estar vacio.'))
			else:			
				s = str(values.get("type_document_id"))
				type_document_id = s.rstrip('0').rstrip('.') if '.' in s else s			
				l10n_latam_search = self.env['l10n_latam.identification.type'].search([('code_sunat','=',type_document_id)])
				if not l10n_latam_search:
					raise UserError("Tipo de Doc. no disponible en el sistema Con Codigo Sunat: "+str(type_document_id))
				else:
					if len(l10n_latam_search)>1:
						raise UserError("Dos Tipos de Documentos Con El Mismo Codigo Sunat en el sistema:"+str(type_document_id))
					else:
						l10n_latam = l10n_latam_search.id
			
				
           
		#partner_repetido = self.env['res.partner'].search([('vat','=',vat),('l10n_latam_identification_type_id','=',l10n_latam),('name','=',values.get('name').strip()),('parent_id','=',parent if parent != False else False)])
		#if partner_repetido:
			#return
		vals = {
							'name':values.get('name').strip(),
							'company_type':type,
							'type':tipo_contacto,
							'parent_id':parent,
							'street':values.get('street').strip(),
							'street2':values.get('street2').strip(),
							'city':values.get('city').strip(),
							'state_id':state,
							'zip':zip_s,
							'country_id':country,
							'l10n_latam_identification_type_id':l10n_latam,
							'vat':vat,
							'website':values.get('website').strip(),
							'phone':phone_v,
							'mobile':mobile_v,
							'email':values.get('email').strip(),
							'user_id':saleperson,
							'ref':ref,
							'property_payment_term_id':cust_pmt_term,
							'property_supplier_payment_term_id':vendor_pmt_term,
							'customer_rank': 1 if is_customer else 0,
							'supplier_rank': 1 if is_supplier else 0,
							'is_customer': is_customer,
							'is_supplier': is_supplier,
							'property_account_receivable_id': property_account_receivable_id,
							'property_account_payable_id': property_account_payable_id,
							'function':values.get('puesto_trabajo').strip() if values.get('puesto_trabajo').strip()!='' else False,
							'title':titulo,
							'comment':values.get('notas').strip() if values.get('notas').strip()!='' else False,
							'is_not_home':is_not_home_v,
							'moneda':moneda,
							'credit_limit':values.get('credit_limit'),
							'company_id':company_id_v
							  }
		
		res = self.env['res.partner'].create(vals)
		return res

	def verify_if_exists_partner(self):
		if self.file:
			file_name = str(self.file_name)
			extension = file_name.split('.')[1]
		if extension not in ['xls','xlsx','XLS','XLSX']:
			raise UserError(_('Cargue solo el archivo xls.!'))
		fp = tempfile.NamedTemporaryFile(delete=False,suffix=".xlsx")
		fp.write(binascii.a2b_base64(self.file))
		fp.seek(0)
		values = {}
		res = {}
		result = []
		workbook = xlrd.open_workbook(fp.name)
		sheet = workbook.sheet_by_index(0)
		for row_no in range(sheet.nrows):
			if row_no <= 0:
				fields = map(lambda row:row.value.encode('utf-8'), sheet.row(row_no))
			else:
				line = list(map(lambda row:isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
				values.update( {'name':line[0],
								'type_document_id': line[9],
								'vat': line[10],
								})
				gg = self.verify_partner(values)
				if gg:
					result.append(gg)
		
		if len(result)>0:
			import io
			from xlsxwriter.workbook import Workbook
			ReportBase = self.env['report.base']

			direccion = self.env['main.parameter'].search([('company_id','=',self.env.company.id)],limit=1).dir_create_file

			if not direccion:
				raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

			workbook = Workbook(direccion +'Partners_Existentes.xlsx')
			workbook, formats = ReportBase.get_formats(workbook)

			import importlib
			import sys
			importlib.reload(sys)

			worksheet = workbook.add_worksheet("Partners")
			worksheet.set_tab_color('blue')

			HEADERS = ['NOMBRE','TIPO DOC','NRO DOC']
			worksheet = ReportBase.get_headers(worksheet,HEADERS,0,0,formats['boldbord'])
			x=1

			for line in result:
				worksheet.write(x,0,line[0] if line[0] else '',formats['especial1'])
				worksheet.write(x,1,line[1] if line[1] else '',formats['especial1'])
				worksheet.write(x,2,line[2] if line[2] else '',formats['especial1'])
				x += 1

			widths = [114,19,12]
			worksheet = ReportBase.resize_cells(worksheet,widths)
			workbook.close()

			f = open(direccion +'Partners_Existentes.xlsx', 'rb')			
			return self.env['popup.it'].get_file('Partners Duplicados.xlsx',base64.encodestring(b''.join(f.readlines())))
		else:			
			return self.env['popup.it'].get_message('NO EXISTEN PARTNERS DUPLICADOS.')

	def verify_partner(self, values):
		l10n_latam = False
		if values.get('type_document_id'):			
			s = str(values.get('type_document_id'))
			type_document_id = s.rstrip('0').rstrip('.') if '.' in s else s
			l10n_latam_search = self.env['l10n_latam.identification.type'].search([('code_sunat','=',type_document_id)])
			if not l10n_latam_search:
				raise UserError("Tipo de Doc. %s no disponible en el sistema"%(type_document_id))
			else:
				if len(l10n_latam_search)>1:
					raise UserError("Dos Tipos de Doc. disponible en el sistema Con Mismo Codigo Sunat" + str(type_document_id))
				else:
					l10n_latam = l10n_latam_search.id

		s = str(values.get('vat')).strip()
		vat = s.rstrip('0').rstrip('.') if '.' in s else s
		search_partner = self.env['res.partner'].search([('vat','=',vat),('l10n_latam_identification_type_id','=',l10n_latam)])
		if search_partner:			
			return [values.get('name'),values.get('type_document_id'),values.get('vat')]
	
	def import_partner(self):
		if self.file:
			file_name = str(self.file_name)
			extension = file_name.split('.')[1]
		if extension not in ['xls','xlsx','XLS','XLSX']:
			raise UserError(_('Cargue solo el archivo xls.!'))
		fp = tempfile.NamedTemporaryFile(delete=False,suffix=".xlsx")
		fp.write(binascii.a2b_base64(self.file))
		fp.seek(0)
		values = {}
		res = {}
		workbook = xlrd.open_workbook(fp.name)
		sheet = workbook.sheet_by_index(0)
		for row_no in range(sheet.nrows):
			if row_no <= 0:
				fields = map(lambda row:row.value.encode('utf-8'), sheet.row(row_no))
			else:
				line = list(map(lambda row:isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
				if self.partner_option == 'create':
					values.update( {'name':line[0],
									'type': line[1],
									'parent': line[2],
									'street': line[3],
									'street2': line[4],
									'city': line[5],
									'state': line[6],
									'zip': line[7],
									'country': line[8],
									'type_document_id': line[9],
									'vat': line[10],
									'website': line[11],
									'phone': line[12],
									'mobile': line[13],
									'email': line[14],
									'customer': line[15],
									'vendor': line[16],
									'saleperson': line[17],
									'ref': line[18],
									'cust_pmt_term': line[19],
									'vendor_pmt_term': line[20],
									'cta_cobrar': line[21],
									'cta_pagar': line[22],
									'tipo_direccion': line[23],
									'puesto_trabajo': line[24],
									'titulo': line[25],
									'notas': line[26],
									'is_not_home':line[27],
									'moneda':line[28],
									'credit_limit':line[29],
									'company_id': line[30]
									})
					res = self.create_partner(values)
				else:
					l10n_latam = False
					if line[0].strip()== '':
						raise UserError('Campo Nombre Obligatorio.')
					if line[30].strip()== '':
						raise UserError('Campo COMPAÑIA Obligatorio.')
					else:
						if ((line[30]).strip() == '1'):
							company_id_v = self.env.company.id
						elif ((line[30]).strip().lower() == 'verdadero'):
							company_id_v = self.env.company.id
						elif ((line[30]).strip().lower() == 'falso'):
							company_id_v = False
						elif ((line[30]).strip() == '0'):
							company_id_v = False
						else:
							raise UserError('Campo COMPAÑIA No Disponible segun formato, usted ingreso: ' + str(line[30]).strip())
						
					
					s = str(line[10]).strip()
					vat = s.rstrip('0').rstrip('.') if '.' in s else s
					s = str(line[18]).strip()
					ref = s.rstrip('0').rstrip('.') if '.' in s else s					
					parent = False
					state = False
					country = False
					saleperson = False
					vendor_pmt_term = False
					cust_pmt_term = False
          				
					if line[27].strip()== '':
						raise UserError('Campo NO DOMICILIADO es Obligatorio')
					else:
						if ((line[27]).strip() == '1'):
							is_not_home_v = True
						elif ((line[27]).strip().lower() == 'verdadero'):
							is_not_home_v = True
						elif ((line[27]).strip().lower() == 'falso'):
							is_not_home_v = False
						elif ((line[27]).strip() == '0'):
							is_not_home_v = False
						else:
							raise UserError('Campo NO DOMICILIADO No Disponible segun formato, usted ingreso: ' + str(line[27]).strip())
					phone_v = False
					if line[12].strip() != '':
						s = str(line[12]).strip()
						phone_v = s.rstrip('0').rstrip('.') if '.' in s else s
					mobile_v = False
					if line[13].strip() != '':
						s = str(line[13]).strip()
						mobile_v = s.rstrip('0').rstrip('.') if '.' in s else s
					moneda = False

					if line[28].strip() != '':
						if line[28].strip() == "USD" or line[28].strip() == "USD (USD)":
							moneda_id = self.env['res.currency'].search([('name','=','USD')])
						elif line[28].strip() == "PEN" or line[28].strip() == "PEN (PEN)":
							moneda_id = self.env['res.currency'].search([('name','=','PEN')])
						else:
							raise UserError('*Recuerde que solo estan disponibles dolares y soles. Campo Moneda Del Credito No Disponible segun formato, usted ingreso: ' + str(line[28]).strip())
						moneda = moneda_id.id
   
					if line[15].strip()== '':
						raise UserError('Campo Cliente es Obligatorio')
					else:
						if ((line[15]).strip() == '1'):
							is_customer = True          
						elif ((line[15]).strip().lower() == 'verdadero'):
							is_customer = True
						elif ((line[15]).strip().lower() == 'falso'):
							is_customer = False
						elif ((line[15]).strip() == '0'):
							is_customer = False
						else:
							raise UserError('Campo Cliente No Disponible segun formato, usted ingreso: ' + str(line[15]).strip())

					if line[16].strip()== '':
						raise UserError('Campo Proveedor es Obligatorio')
					else:
						if ((line[16]).strip() == '1'):
							is_supplier = True
						elif ((line[16]).strip().lower() == 'verdadero'):
							is_supplier = True
						elif ((line[16]).strip().lower() == 'falso'):
							is_supplier = False
						elif ((line[16]).strip() == '0'):
							is_supplier = False
						else:
							raise UserError('Campo Proveedor No Disponible segun formato, usted ingreso: ' + str(line[16]).strip())
					if line[23]:
						if line[23].strip() == 'contact':
							tipo_contacto = 'contact'
						elif line[23].strip() == 'invoice':
							tipo_contacto = 'invoice'
						elif line[23].strip() == 'delivery':
							tipo_contacto = 'delivery'
						elif line[23].strip() == 'other':
							tipo_contacto = 'other'
						elif line[23].strip() == 'private':
							tipo_contacto = 'private'
						else:
							raise UserError(_('"%s" Tipo de Dirección no Disponible.') % line[23])
					else:
						raise UserError("El Campo Tipo de Dirección no puede estar vacio")
					parent = False					
					if line[0].strip()== '':
						raise UserError('Campo Nombre Obligatorio.')
					
					if line[6]:
						state = self.find_state(line)
					if line[8]:
						country = self.find_country(line)
					if line[17]:
						saleperson_search = self.env['res.users'].search([('name','=',line[17].strip())])
						if not saleperson_search:
							raise UserError(_('"%s" Usuario no Disponible en el Sistema.') % line[17])							
						else:
							if len(saleperson_search)>1:
								raise UserError(_('"%s" Dos Usuario Disponibles en el Sistema.') % line[17])
							else:
								saleperson = saleperson_search.id
					if line[19]:
						cust_payment_term_search = self.env['account.payment.term'].search([('name','=',line[19].strip())])
						if not cust_payment_term_search:
							raise UserError(u"Término de pago Cliente no disponible en el sistema" + str(line[19].strip()))
						else:
							if len(cust_payment_term_search)>1:
								raise UserError(u"Dos Término de pago Cliente disponible en el sistema"+ str(line[19].strip()))
							else:
								cust_pmt_term = cust_payment_term_search.id
					if line[20]:
						vendor_payment_term_search = self.env['account.payment.term'].search([('name','=',line[20].strip())])
						if not vendor_payment_term_search:
							raise UserError(u"Término de pago PROVEEDOR no disponible en el sistema" + str(line[20].strip()))
						else:
							if len(cust_payment_term_search)>1:
								raise UserError(u"Dos Término de pago PROVEEDOR disponible en el sistema"+ str(line[20].strip()))
							else:
								vendor_pmt_term = vendor_payment_term_search.id

					property_account_receivable_id = None
					property_account_payable_id = None
					titulo=False
					ubigeo = False
					if line[7]:
						s = str(line[7]).strip()
						ubigeo = s.rstrip('0').rstrip('.') if '.' in s else s
     
					if line[21]:
						s = str(line[21]).strip()
						account_in = s.rstrip('0').rstrip('.') if '.' in s else s
						property_account_receivable_id = self.find_account(account_in)

					if line[22]:
						s = str(line[22]).strip()
						account_ex = s.rstrip('0').rstrip('.') if '.' in s else s
						property_account_payable_id = self.find_account(account_ex)
					if line[1].strip() != '':
						if line[1].strip() == 'company' or line[1].strip().lower() == 'compañía' or line[1].strip().lower() == 'compañia':
							if tipo_contacto != 'contact':
								raise UserError('No puede Puede crear un contacto tipo compañia y no ser de tipo direccion Contacto: '+str(line[0]))
							if line[24]:
								raise UserError('No puede Tener Puesto De Trabajo Si es Contacto tipo Compañia: '+str(line[0]))
							if line[25]:
								raise UserError('No puede Tener Titulo Si es un Contacto Tipo Compañia: '+str(line[0]))
							if line[2]:
								raise UserError('No puede dar padre si ha seleccionado el tipo de empresa: '+str(line[0]))
							type =  'company'
						elif line[1].strip() == 'person' or line[1].strip().lower() == 'individual':
							type =  'person'
							if line[25]:
								titulo_ids = self.env['res.partner.title'].sudo().search([('name','=',line[25].strip())])
								if titulo_ids:
									if len(titulo_ids)>1:
										raise UserError('Dos Titulos Con Mismo Nombre: '+str(line[25]))
									else:
										titulo = titulo_ids.id
								else:
									raise UserError('Titulo no Encontrado: '+str(line[25]))
							parent = False
							abuelo = False					
							if line[2]:
								for i in line[2].split('|'):
									#parent_search = self.env['res.partner'].search([('vat','=',vat),('l10n_latam_identification_type_id','=',l10n_latam),('parent_id','=',abuelo),('name','=',str(i).strip())])
									parent_search = self.env['res.partner'].search([('parent_id','=',abuelo),('name','=',str(i).strip())])
									if parent_search:
										if len(parent_search)>1:
											raise UserError("Dos Contactos Padre Con Mismo Nombre: "+str(str(i).strip()))
										parent =  parent_search.id
										abuelo = parent_search.id
									else:
										raise UserError(_('"%s" Contacto Padre no Encontrado.') %(str(i).strip()))
						else:
							raise UserError('Tipo de Contacto No Disponible: '+str(line[1]))
					else:
						raise UserError('Campo Tipo Contacto No puede estar Vacio')
					l10n_latam = False
					if type=='person':
						if parent == False:
							if line[9].strip()== '':
								raise UserError('Campo TIPO DE DOCUMENTO Obligatorio.')
							else:
								s = str(line[9])
								type_document_id = s.rstrip('0').rstrip('.') if '.' in s else s
								l10n_latam_search = self.env['l10n_latam.identification.type'].search([('code_sunat','=',type_document_id)])
								if not l10n_latam_search:
									raise UserError("Tipo de Doc. Con Codigo Sunat %s no disponible en el sistema"%(type_document_id))
								else:
									if len(l10n_latam_search)>1:
										raise UserError("Dos Tipo de Doc. Con Codigo Sunat %s disponible en el sistema"%(type_document_id))
									else:
										l10n_latam = l10n_latam_search.id
						else:
							padre_obj = self.env['res.partner'].search([('id','=',parent)])
							l10n_latam = padre_obj.l10n_latam_identification_type_id.id
					else:
						if line[9].strip()== '':
							raise UserError('Campo TIPO DE DOCUMENTO Obligatorio.')
						else:
							s = str(line[9])
							type_document_id = s.rstrip('0').rstrip('.') if '.' in s else s
							l10n_latam_search = self.env['l10n_latam.identification.type'].search([('code_sunat','=',type_document_id)])
							if not l10n_latam_search:
								raise UserError("Tipo de Doc. Con Codigo Sunat %s no disponible en el sistema"%(type_document_id))
							else:
								if len(l10n_latam_search)>1:
									raise UserError("Dos Tipo de Doc. Con Codigo Sunat %s disponible en el sistema"%(type_document_id))
								else:
									l10n_latam = l10n_latam_search.id
						
								
     
     
					search_partner = self.env['res.partner'].search([('vat','=',vat),('l10n_latam_identification_type_id','=',l10n_latam),('name','=',line[0].strip()),('parent_id','=',parent if parent != False else False)])
					if not search_partner:
						raise UserError("No Existe Un Contacto con Nombre: "+str(line[0])+ "Tipo de Documento con id: " + str(l10n_latam) + " Número De Documento: " + str(vat))
					else:
						if len(search_partner)>1:
							raise UserError("Existe dos Contacto con Nombre: "+str(line[0])+ "Tipo de Documento con id: " + str(l10n_latam) + " Número De Documento: " + str(vat))

					search_partner.write({'type':tipo_contacto,
										'company_type': type,
										'street': line[3].strip(),
										'street2': line[4].strip(),
										'city': line[5].strip(),
										'state_id': state,
										'zip': ubigeo,
										'country_id': country,
										'website': line[11].strip(),
										'phone': phone_v,
										'mobile':mobile_v,
										'email': line[14].strip(),
										'is_customer': is_customer,
										'is_supplier':is_supplier,
          								'user_id':saleperson,
										'ref':ref,
										'property_payment_term_id':cust_pmt_term or False,
										'property_supplier_payment_term_id':vendor_pmt_term or False,
										'property_account_receivable_id':property_account_receivable_id,
										'property_account_payable_id':property_account_payable_id,
										'function':line[24].strip() if line[24].strip()!='' else False,
										'title':titulo,
										'comment':line[26].strip() if line[26].strip()!='' else False,
										'is_not_home':is_not_home_v,
										'moneda':moneda,
										'credit_limit':line[29],
										'company_id':company_id_v
            									})
					if search_partner.customer_rank < 1 and is_customer:
							search_partner.write({'customer_rank':1})
					if search_partner.supplier_rank < 1 and is_supplier:
						search_partner.write({'supplier_rank':1})
		
		return self.env['popup.it'].get_message('SE IMPORTARON LOS PARTNERS DE MANERA CORRECTA.')

	def find_account(self, code):
		account_obj = self.env['account.account']
		account_search = account_obj.search([('code', '=', str(code)),('company_id','=',self.env.company.id)])
		if account_search:
			if len(account_search)>1:
				raise UserError(_('Dos Cuentas con el Codigo "%s" en esta Compañia') % code)
			else:
				return account_search.id
		else:
			raise UserError(_('No existe una Cuenta con el Codigo "%s" en esta Compañia') % code)

	def download_template(self):
		return {
			 'type' : 'ir.actions.act_url',
			 'url': '/web/binary/download_partner_import_template_s',
			 'target': 'new',
			 }
