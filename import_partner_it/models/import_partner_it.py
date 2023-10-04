# -*- coding: utf-8 -*-

import tempfile
import binascii
import xlrd
from odoo.exceptions import UserError
from odoo import models, fields, exceptions, api, _
import base64

class ImportPartnerIt(models.TransientModel):
	_name = 'import.partner.it'

	file = fields.Binary('Archivo')
	file_name = fields.Char()
	partner_option = fields.Selection([('create','Crear Partner'),('update','Actualizar Partner')],string='Opcion', required=True,default="create")
	
	def find_country(self,val):
		if type(val) == dict:
			country_search = self.env['res.country'].search([('name','=',val.get('country'))],limit=1)
			if country_search:
				return country_search.id
			else:
				raise UserError(u'El país %s no está disponible en el sistema.'%(val.get('country')))
		else:
			country_search = self.env['res.country'].search([('name','=',val[8])],limit=1)
			if country_search:
				return country_search.id
			else:
				raise UserError(u'El país %s no está disponible en el sistema.'%(val[8]))
	
	def find_state(self,val):
		if type(val) == dict:
			state_search = self.env['res.country.state'].search([('name','=',val.get('state'))],limit=1)
			if state_search:
				return state_search.id
			else:
				raise UserError(u'El estado %s no está disponible en el sistema.'%(val.get('state')))
		else:
			state_search = self.env['res.country.state'].search([('name','=',val[6])],limit=1)
			if state_search:
				return state_search.id
			else:
				raise UserError(u'El estado %s no está disponible en el sistema.'%(val[6]))

	def create_partner(self, values):
		parent = state = country = l10n_latam = saleperson =  vendor_pmt_term = cust_pmt_term = False
		if values.get('type') == 'company':
			if values.get('parent'):
				raise UserError('No puede dar padre si ha seleccionado el tipo de empresa')
			type =  'company'
		else:
			type =  'person'
			if values.get('parent'):
				parent_search = self.env['res.partner'].search([('name','=',values.get('parent'))],limit=1)
				if parent_search:
					parent =  parent_search.id
				else:
					raise UserError("Contacto Padre no disponible")
		if values.get('state'):
			state = self.find_state(values)
		if values.get('country'):
			country = self.find_country(values)

		if values.get('type_document_id'):
			s = str(values.get("type_document_id"))
			type_document_id = s.rstrip('0').rstrip('.') if '.' in s else s
			l10n_latam_search = self.env['l10n_latam.identification.type'].search([('code_sunat','=',type_document_id)],limit=1)
			if not l10n_latam_search:
				raise UserError("Tipo de Doc. no disponible en el sistema")
			else:
				l10n_latam = l10n_latam_search.id
		
		if values.get('saleperson'):
			saleperson_search = self.env['res.users'].search([('name','=',values.get('saleperson'))],limit=1)
			if not saleperson_search:
				raise UserError("Usuario no disponible en el sistema")
			else:
				saleperson = saleperson_search.id
		if values.get('cust_pmt_term'):
			cust_payment_term_search = self.env['account.payment.term'].search([('name','=',values.get('cust_pmt_term'))],limit=1)
			if cust_payment_term_search:
				cust_pmt_term = cust_payment_term_search.id
		if values.get('vendor_pmt_term'):
			vendor_payment_term_search = self.env['account.payment.term'].search([('name','=',values.get('vendor_pmt_term'))],limit=1)
			
			if vendor_payment_term_search:
				vendor_pmt_term = vendor_payment_term_search.id
		is_customer = False
		is_supplier = False
		is_employee = False
		if ((values.get('customer')) == '1'):
			is_customer = True
			
		if ((values.get('vendor')) == '1'):
			is_supplier = True

		if ((values.get('employee')) == '1'):
			is_employee = True
			
		if ((values.get('customer')) == 'SI'):
			is_customer = True
			
		if ((values.get('vendor')) == 'SI'):
			is_supplier = True

		if ((values.get('employee')) == 'SI'):
			is_employee = True

		if str(values.get('partner_id')) == '':
			raise UserError(_('El campo "partner_id" no puede estar vacio.'))

		s = str(values.get("vat"))
		vat = s.rstrip('0').rstrip('.') if '.' in s else s

		s = str(values.get("ref"))
		ref = s.rstrip('0').rstrip('.') if '.' in s else s

		property_account_receivable_id = None
		property_account_payable_id = None

		if values.get("cta_cobrar"):
			property_account_receivable_id = self.find_account(values.get("cta_cobrar"))

		if values.get("cta_pagar"):
			property_account_payable_id = self.find_account(values.get("cta_pagar"))
		   
		vals = {
				'name':values.get('name'),
				'company_type':type,
				'parent_id':parent,
				'street':values.get('street'),
				'street2':values.get('street2'),
				'city':values.get('city'),
				'state_id':state,
				'zip':values.get('zip'),
				'country_id':country,
				'l10n_latam_identification_type_id':l10n_latam,
				'vat':vat,
				'website':values.get('website'),
				'phone':values.get('phone'),
				'mobile':values.get('mobile'),
				'email':values.get('email'),
				'user_id':saleperson,
				'ref':ref,
				'property_payment_term_id':cust_pmt_term,
				'property_supplier_payment_term_id':vendor_pmt_term,
				'customer_rank': 1 if is_customer else 0,
				'supplier_rank': 1 if is_supplier else 0,
				'is_customer': is_customer,
				'is_supplier': is_supplier,
				'is_employee': is_employee
				}
		if property_account_receivable_id:
			vals['property_account_receivable_id'] = property_account_receivable_id
		if property_account_payable_id:
			vals['property_account_payable_id'] = property_account_payable_id
		partner_search = self.env['res.partner'].search([('name','=',values.get('name'))],limit=1) 
		if partner_search:
			raise UserError(_('"%s" Partner ya existe.') % values.get('name'))  
		else:      	
			res = self.env['res.partner'].create(vals)
			return res

	def verify_if_exists_partner(self):
		extension = ''
		if self.file:
			file_name = str(self.file_name)
			extension = file_name.split('.')[1]
		if extension not in ['xls','xlsx','XLS','XLSX']:
			raise UserError(_('Cargue solo el archivo xls o xlsx.!'))
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

			direccion = self.env['account.main.parameter'].search([('company_id','=',self.env.company.id)],limit=1).dir_create_file

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
			return self.env['popup.it'].get_file('Partners Duplicados.xlsx',base64.encodebytes(b''.join(f.readlines())))

		else:
			return self.env['popup.it'].get_message('NO EXISTEN PARTNERS DUPLICADOS.')

	def verify_partner(self, values):
		l10n_latam = False
		if values.get('type_document_id'):
			s = str(values.get('type_document_id'))
			type_document_id = s.rstrip('0').rstrip('.') if '.' in s else s
			l10n_latam_search = self.env['l10n_latam.identification.type'].search([('code_sunat','=',type_document_id)],limit=1)
			if not l10n_latam_search:
				raise UserError("Tipo de Doc. %s no disponible en el sistema"%(type_document_id))
			else:
				l10n_latam = l10n_latam_search.id

		s = str(values.get('vat'))
		vat = s.rstrip('0').rstrip('.') if '.' in s else s
		search_partner = self.env['res.partner'].search([('vat','=',vat),('l10n_latam_identification_type_id','=',l10n_latam)],limit=1)
		if search_partner:
			return [values.get('name'),values.get('type_document_id'),values.get('vat')]
	
	def import_partner(self):
		extension = ''
		if self.file:
			file_name = str(self.file_name)
			extension = file_name.split('.')[1]
		if extension not in ['xls','xlsx','XLS','XLSX']:
			raise UserError(_('Cargue solo el archivo xls o xlsx.!'))
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
									'employee': line[17],
									'saleperson': line[18],
									'ref': line[19],
									'cust_pmt_term': line[20],
									'vendor_pmt_term': line[21],
									'cta_cobrar': line[22],
									'cta_pagar': line[23],
									})
					res = self.create_partner(values)
				else:
					l10n_latam = False
					if line[9]:
						s = str(line[9])
						type_document_id = s.rstrip('0').rstrip('.') if '.' in s else s
						l10n_latam_search = self.env['l10n_latam.identification.type'].search([('code_sunat','=',type_document_id)],limit=1)
						if not l10n_latam_search:
							raise UserError("Tipo de Doc. %s no disponible en el sistema"%(type_document_id))
						else:
							l10n_latam = l10n_latam_search.id

					s = str(line[10])
					vat = s.rstrip('0').rstrip('.') if '.' in s else s
					s = str(line[19])
					ref = s.rstrip('0').rstrip('.') if '.' in s else s
					search_partner = self.env['res.partner'].search([('vat','=',vat),('l10n_latam_identification_type_id','=',l10n_latam)],limit=1)
					if not search_partner:
						raise UserError('No existe un partner con Nro de Documento "%s" para actualizar'%(vat))
					parent = False
					state = False
					country = False
					saleperson = False
					vendor_pmt_term = False
					cust_pmt_term = False

					is_customer = False
					is_supplier = False
					is_employee = False

					if ((line[15]) == '1'):
						is_customer = True
						
					if ((line[16]) == '1'):
						is_supplier = True

					if ((line[17]) == '1'):
						is_employee = True
						
					if ((line[15]) == 'SI'):
						is_customer = True
						
					if ((line[16]) == 'SI'):
						is_supplier = True
					
					if ((line[17]) == 'SI'):
						is_employee = True
							
					if line[1] == 'company':
						if line[2]:
							raise UserError('No puede dar padre si ha seleccionado el tipo de empresa')
						type =  'company'
					else:
						type =  'person'
						if line[2]:
							parent_search = self.env['res.partner'].search([('vat','=',line[2])],limit=1)
							if parent_search:
								parent =  parent_search.id
							else:
								raise UserError("Contacto padre con Nro de Documento '%s' no disponible"%(line[2]))
					
					if line[6]:
						state = self.find_state(line)
					if line[8]:
						country = self.find_country(line)
					if line[18]:
						saleperson_search = self.env['res.users'].search([('name','=',line[18])],limit=1)
						if not saleperson_search:
							raise UserError("Usuario no disponible en el sistema")
						else:
							saleperson = saleperson_search.id
					if line[20]:
						cust_payment_term_search = self.env['account.payment.term'].search([('name','=',line[20])],limit=1)
						if not cust_payment_term_search:
							raise UserError(u"Término de pago no disponible en el sistema")
						else:
							cust_pmt_term = cust_payment_term_search.id
					if line[21]:
						vendor_payment_term_search = self.env['account.payment.term'].search([('name','=',line[21])],limit=1)
						if not vendor_payment_term_search:
							raise UserError(u"Término de pago no disponible en el sistema")
						else:
							vendor_pmt_term = vendor_payment_term_search.id

					property_account_receivable_id = None
					property_account_payable_id = None

					if line[22]:
						property_account_receivable_id = self.find_account(line[22])

					if line[23]:
						property_account_payable_id = self.find_account(line[23])
					
					search_partner.name = line[0]
					search_partner.company_type = type
					search_partner.parent_id = parent or False
					search_partner.street = line[3]
					search_partner.street2 = line[4]
					search_partner.city = line[5]
					search_partner.state_id = state
					search_partner.zip = line[7]
					search_partner.country_id = country
					search_partner.website = line[11]
					search_partner.phone = line[12]
					search_partner.mobile = line[13]
					search_partner.email = line[14]
					search_partner.is_customer = is_customer
					search_partner.is_supplier = is_supplier
					search_partner.is_employee = is_employee
					if search_partner.customer_rank < 1 and is_customer:
						search_partner.customer_rank = 1
					if search_partner.supplier_rank < 1 and is_supplier:
						search_partner.supplier_rank = 1
					search_partner.user_id = saleperson
					search_partner.ref = ref
					search_partner.property_payment_term_id = cust_pmt_term or False
					search_partner.property_supplier_payment_term_id = vendor_pmt_term or False
					if property_account_receivable_id:
						search_partner.property_account_receivable_id = property_account_receivable_id
					if property_account_payable_id:
						search_partner.property_account_payable_id = property_account_payable_id
		
		return self.env['popup.it'].get_message('SE IMPORTARON LOS PARTNERS DE MANERA CORRECTA.')

	def find_account(self, code):
		account_obj = self.env['account.account']
		account_search = account_obj.search([('code', '=', str(code)),('company_id','=',self.env.company.id)],limit=1)
		if account_search:
			return account_search.id
		else:
			raise UserError(_('No existe una Cuenta con el Codigo "%s" en esta Compañia') % code)

	def download_template(self):
		return {
			 'type' : 'ir.actions.act_url',
			 'url': '/web/binary/download_partner_import_template',
			 'target': 'new',
			 }