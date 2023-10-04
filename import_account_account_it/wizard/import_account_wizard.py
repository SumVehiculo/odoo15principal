# -*- coding: utf-8 -*-

import tempfile
import binascii
import xlrd
from odoo.exceptions import UserError
from odoo import models, fields, _

class ImportAccountWizard(models.TransientModel):
	_name = "import.account.wizard"

	File_slect = fields.Binary(string="Archivo")
	type_import = fields.Selection([('import','Importar Cuentas'),('copy',u'Copiar a partir de una Compañía')],string='Tipo', required=True,default="import")
	company_id = fields.Many2one('res.company',string=u'Compañia Origen', default=lambda self: self.env.company)
	company_copy_id = fields.Many2one('res.company',string=u'Compañia Destino')

	def copy_accounts(self):
		if not self.env.user.has_group('base.group_multi_company'):
			raise UserError(u'Usted debe tener el permiso Multicompañía para realizar esta acción.')
		if 'create_asset' in self.env['account.account']._fields:
			self.env.cr.execute(""" 
				INSERT INTO ACCOUNT_ACCOUNT (NAME,CODE,CURRENCY_ID,ROOT_ID,DEPRECATED,USER_TYPE_ID,INTERNAL_TYPE,INTERNAL_GROUP,RECONCILE,NOTE,COMPANY_ID,
				GROUP_ID,M_CLOSE,ACCOUNT_TYPE_IT_ID,ACCOUNT_TYPE_CASH_ID,PATRIMONY_ID,TYPE_ADQUISITION,CHECK_MOORAGE,
				IS_DOCUMENT_AN, FINANCIAL_ENTITY, CODE_SUNAT, CODE_BANK, ACCOUNT_NUMBER, CLASIFICATION_SHEET, CREATE_ASSET)
				SELECT NAME,CODE,CURRENCY_ID,ROOT_ID,DEPRECATED,USER_TYPE_ID,INTERNAL_TYPE,INTERNAL_GROUP,RECONCILE,NOTE, %d AS COMPANY_ID,
				GROUP_ID,M_CLOSE,ACCOUNT_TYPE_IT_ID,ACCOUNT_TYPE_CASH_ID,PATRIMONY_ID,TYPE_ADQUISITION,CHECK_MOORAGE,
				IS_DOCUMENT_AN, FINANCIAL_ENTITY, CODE_SUNAT, CODE_BANK, ACCOUNT_NUMBER, CLASIFICATION_SHEET, CREATE_ASSET FROM ACCOUNT_ACCOUNT
				WHERE COMPANY_ID = %d;
				""" % (self.company_copy_id.id,self.company_id.id))
		else:
			self.env.cr.execute(""" 
				INSERT INTO ACCOUNT_ACCOUNT (NAME,CODE,CURRENCY_ID,ROOT_ID,DEPRECATED,USER_TYPE_ID,INTERNAL_TYPE,INTERNAL_GROUP,RECONCILE,NOTE,COMPANY_ID,
				GROUP_ID,M_CLOSE,ACCOUNT_TYPE_IT_ID,ACCOUNT_TYPE_CASH_ID,PATRIMONY_ID,TYPE_ADQUISITION,CHECK_MOORAGE,
				IS_DOCUMENT_AN, FINANCIAL_ENTITY, CODE_SUNAT, CODE_BANK, ACCOUNT_NUMBER, CLASIFICATION_SHEET)
				SELECT NAME,CODE,CURRENCY_ID,ROOT_ID,DEPRECATED,USER_TYPE_ID,INTERNAL_TYPE,INTERNAL_GROUP,RECONCILE,NOTE, %d AS COMPANY_ID,
				GROUP_ID,M_CLOSE,ACCOUNT_TYPE_IT_ID,ACCOUNT_TYPE_CASH_ID,PATRIMONY_ID,TYPE_ADQUISITION,CHECK_MOORAGE,
				IS_DOCUMENT_AN, FINANCIAL_ENTITY, CODE_SUNAT, CODE_BANK, ACCOUNT_NUMBER, CLASIFICATION_SHEET FROM ACCOUNT_ACCOUNT
				WHERE COMPANY_ID = %d;
				""" % (self.company_copy_id.id,self.company_id.id))

		return self.env['popup.it'].get_message('SE DUPLICARON TODAS LAS CUENTAS EN EL COMPAÑÍA %s.'%(self.company_copy_id.name))
	
	def import_file(self):
		try:
			fp = tempfile.NamedTemporaryFile(delete= False,suffix=".xlsx")
			fp.write(binascii.a2b_base64(self.File_slect))
			fp.seek(0)
			values = {}
			workbook = xlrd.open_workbook(fp.name)
			sheet = workbook.sheet_by_index(0)

		except:
			raise UserError(_("Archivo invalido!"))

		for row_no in range(sheet.nrows):
			if row_no <= 0:
				continue
			else:
				
				line = list(map(lambda row:isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))

				values.update( {'code' : line[0],
								'name' : line[1],
								'user' : line[2],
								'tax'  : line[3],
								'tag'  : line[4],
								'group': line[5],
								'currency' :line[6],
								'reconcile':line[7],
								'deprecat' :line[8],
								'tipo_ef' : line[9],
								'metodo_cierre' : line[10],
								'cuenta_cierre' : line[11],
								'tipo_fe' : line[12],
								'tiene_destino' : line[13],
								'a_debe' : line[14],
								'a_haber' : line[15],
								'es_analisis' : line[16],
								'clasificacion_ht' : line[17],
								'code_sunat' : line[18],
								})

				res = self.create_chart_accounts(values)
		
		return self.env['popup.it'].get_message(u'SE IMPORTO CON EXITO LAS CUENTAS')
	
	def create_chart_accounts(self,values):

		if values.get("code") == "":
			raise UserError(_('El campo de code no puede estar vacío.') )

		account_obj = self.env['account.account']
		account_search = account_obj.search([
			('code', '=', values.get("code")),('company_id','=',self.env.company.id)
			])

		if account_search:
			if values.get("name") or values.get("name") != "":
				account_search.write({'name': values.get("name")})
			if values.get("user") or values.get("user") != "":
				user_id = self.find_user_type(values.get('user'))
				account_search.write({'user_type_id': user_id.id})
			if values.get("tax") or values.get("tax") != "":
				tax_ids = self.get_tax_ids(values.get('tax'))
				account_search.write({'tax_ids': [(6,0,[y.id for y in tax_ids])]})
			if values.get("tag") or values.get("tag") != "":
				tag_ids = self.get_tax_ids(values.get('tag'))
				account_search.write({'tag_ids': [(6,0,[y.id for y in tag_ids])]})
			if values.get("group") or values.get("group") != "":
				group_get = self.find_group(values.get('group'))
				account_search.write({'group_id': group_get.id})
			if values.get("currency") or values.get("currency") != "":
				currency_get = self.find_currency(values.get('currency'))
				account_search.write({'currency_id':currency_get})
			if values.get("reconcile") or values.get("reconcile") != "":
				is_reconcile = False
				if values.get("reconcile") == 'TRUE' or values.get("reconcile") == "1":
					is_reconcile = True
				account_search.write({'reconcile':is_reconcile})
			if values.get("deprecat") or values.get("deprecat") != "":
				is_deprecated = False
				if values.get("deprecat") == 'TRUE' or values.get("deprecat") == "1":
					is_deprecated = True
				account_search.write({'deprecated':is_deprecated})
			if values.get("tipo_ef") or values.get("tipo_ef") != "":
				tipo_ef = self.find_tipo_ef(str(values.get('tipo_ef')))
				account_search.write({'account_type_it_id':tipo_ef})
			if values.get("metodo_cierre") or values.get("metodo_cierre") != "":
				account_search.write({'m_close':str(values.get('metodo_cierre'))})
			if values.get("cuenta_cierre") or values.get("cuenta_cierre") != "":
				cuenta_cierre = self.find_cuenta(str(values.get('cuenta_cierre')))
				account_search.write({'account_close_id':cuenta_cierre})
			if values.get("tipo_fe") or values.get("tipo_fe") != "":
				tipo_fe = self.find_tipo_fe(str(values.get('tipo_fe')))
				account_search.write({'account_type_cash_id':tipo_fe})
			if values.get("tiene_destino") or values.get("tiene_destino") != "":
				is_destiny = False
				if values.get("tiene_destino") == 'TRUE' or values.get("tiene_destino") == "1":
					is_destiny = True
				account_search.write({'check_moorage':is_destiny})
			if values.get("a_debe") or values.get("a_debe") != "":
				a_debe = self.find_cuenta(str(values.get('a_debe')))
				account_search.write({'a_debit':a_debe})
			if values.get("a_haber") or values.get("a_haber") != "":
				a_haber = self.find_cuenta(str(values.get('a_haber')))
				account_search.write({'a_credit':a_haber})
			if values.get("es_analisis") or values.get("es_analisis") != "":
				is_document_an = False
				if values.get("es_analisis") == 'TRUE' or values.get("es_analisis") == "1":
					is_document_an = True
				account_search.write({'is_document_an':is_document_an})
			if values.get("clasificacion_ht") or values.get("clasificacion_ht") != "":
				account_search.write({'clasification_sheet':str(values.get('clasificacion_ht'))})
			if values.get("code_sunat") or values.get("code_sunat") != "":
				account_search.write({'code_sunat':str(values.get('code_sunat'))})
			return account_search
		else:
			if values.get("name") == "":
				raise UserError(_('El campo name no puede estar vacío si se va a crear una cuenta.') )

			if values.get("user") == "":
				raise UserError(_('El campo type no puede estar vacío si se va a crear una cuenta.'))
			is_reconcile = False
			is_deprecated= False
			is_destiny = False
			is_document_an = False

			if values.get("reconcile") == 'TRUE' or values.get("reconcile") == "1":
				is_reconcile = True

			if values.get("deprecat") == 'TRUE'  or values.get("deprecat") == "1":
				is_deprecated = True

			if values.get("tiene_destino") == 'TRUE'  or values.get("tiene_destino") == "1":
				is_destiny = True

			if values.get("es_analisis") == 'TRUE'  or values.get("es_analisis") == "1":
				is_document_an = True

			user_id = self.find_user_type(values.get('user'))
			currency_get = self.find_currency(values.get('currency'))
			group_get = self.find_group(values.get('group'))
			tipo_ef = self.find_tipo_ef(str(values.get('tipo_ef')))
			cuenta_cierre = self.find_cuenta(str(values.get('cuenta_cierre')))
			tipo_fe = self.find_tipo_fe(str(values.get('tipo_fe')))
			a_debe = self.find_cuenta(str(values.get('a_debe')))
			a_haber = self.find_cuenta(str(values.get('a_haber')))

	# --------tax
			tax_ids = self.get_tax_ids(values.get('tax'))
	# --------tag
			tag_ids = self.get_tag_ids(values.get('tag'))

			data = {
					'code' : values.get("code"),
					'name' : values.get('name'),
					'user_type_id':user_id.id,
					'internal_type':user_id.type,
					'internal_group':user_id.internal_group,
					'tax_ids':[(6,0,[y.id for y in tax_ids])]if values.get('tax') else False,	
					'tag_ids':[(6,0,[x.id for x in tag_ids])]if values.get('tag') else False,
					'group_id':group_get.id,
					'currency_id':currency_get or False,
					'reconcile':is_reconcile,
					'deprecated':is_deprecated,
					'account_type_it_id':tipo_ef,
					'm_close':str(values.get('metodo_cierre')) or False,
					'account_close_id':cuenta_cierre or False,
					'account_type_cash_id':tipo_fe or False,
					'check_moorage':is_destiny,
					'a_debit':a_debe or False,
					'a_credit':a_haber or False,
					'is_document_an':is_document_an,
					'clasification_sheet':str(values.get('clasificacion_ht')) or False,
					'code_sunat':str(values.get('code_sunat')) or False,
					}
			chart_id = account_obj.create(data)		

			return chart_id

# ---------------------------user-----------------

	
	def find_user_type(self,user):
		user_type=self.env['account.account.type']
		user_search = user_type.search([('name','=',user)],limit=1)
		if not user_search:
			name = self.env['ir.translation'].search([('value','=',user),('name','=','account.account.type,name')],limit=1)
			user_search = user_type.search([('name','=',name.src)],limit=1)

		if user_search:
			return user_search
		else:
			raise UserError(user)

# --------------------currency--------------------

	
	def find_currency(self, name):
		currency_obj = self.env['res.currency']
		currency_search = currency_obj.search([('name', '=', name)])
		if currency_search:
			return currency_search.id
		else:
			if name == "":
				pass
			else:
				raise UserError(_(' %s Moneda no disponible.') % name)

# --------------------group--------------------

	
	def find_group(self,group):
		group_type=self.env['account.group']
		group_search = group_type.search([('code_prefix_start','=',group)])

		if group_search:
			return group_search
		else:
			raise UserError('No existe el grupo %s' % group)

# -------------------tipo_ef--------------------

	def find_tipo_ef(self,tipo_ef):
		tipo_ef_search = self.env['account.type.it'].search([('code','=',tipo_ef)],limit=1)
		if tipo_ef_search:
			return tipo_ef_search.id
		else:
			if tipo_ef == "":
				pass
			else:
				raise UserError(_(' %s Tipo Estado Financiero no disponible.') % tipo_ef)

# --------------------cuenta--------------------

	def find_cuenta(self,cuenta):
		cuenta_search = self.env['account.account'].search([('code','=',cuenta),('company_id','=',self.env.company.id)],limit=1)
		if cuenta_search:
			return cuenta_search.id
		else:
			if cuenta == "":
				pass
			else:
				raise UserError(_(' %s Cuenta Contable no disponible.') % cuenta)

# --------------------tipo_fe--------------------

	def find_tipo_fe(self,tipo_fe):
		tipo_fe_search = self.env['account.efective.type'].search([('code','=',tipo_fe)],limit=1)
		if tipo_fe_search:
			return tipo_fe_search.id
		else:
			if tipo_fe == "":
				pass
			else:
				raise UserError(_(' %s Tipo Flujo de Efectivo no disponible.') % tipo_fe)

# --------------------tax_ids--------------------
	def get_tax_ids(self,tax_ids):
		tax_ids = []
		if tax_ids:
			if ';' in  tax_ids:
				tax_names = tax_ids.split(';')
				for name in tax_names:
					tax= self.env['account.tax'].search([('name', '=', name)])
					if not tax:
						raise UserError(_('%s No existe el impuesto en su sistema') % name)
					for t in tax:
						tax_ids.append(t)

			elif ',' in  tax_ids:
				tax_names = tax_ids.split(',')
				for name in tax_names:
					tax= self.env['account.tax'].search([('name', '=', name)])
					if not tax:
						raise UserError(_('%s No existe el impuesto en su sistema') % name)
					for t in tax:
						tax_ids.append(t)
			else:
				tax_names = tax_ids.split(',')
				tax= self.env['account.tax'].search([('name', '=', tax_names)])
				if not tax:
					raise UserError(_('"%s" No existe el impuesto en su sistema') % tax_names)
				for t in tax:
					tax_ids.append(t)
		return tax_ids

# --------------------tag_ids--------------------
	def get_tag_ids(self,tag_ids):
		tag_ids = []
		if tag_ids:
			if ';' in  tag_ids:
				tag_names = tag_ids.split(';')
				for name in tag_names:
					tag= self.env['account.account.tag'].search([('name', '=', name)])
					if not tag:
						raise UserError(_('"%s" No existe el etiqueta en su sistema') % name)
					tag_ids.append(tag)

			elif ',' in  tag_ids:
				tag_names = tag_ids.split(',')
				for name in tag_names:
					tag= self.env['account.account.tag'].search([('name', '=', name)])
					if not tag:
						raise UserError(_('"%s" No existe el etiqueta en su sistema') % name)
					tag_ids.append(tag)
			else:
				tag_names = tag_ids.split(',')
				tag= self.env['account.account.tag'].search([('name', '=', tag_names)])
				if not tag:
					raise UserError(_('"%s" No existe el etiqueta en su sistema') % tag_names)
				tag_ids.append(tag)

		return tag_ids

	def download_template(self):
		return {
			 'type' : 'ir.actions.act_url',
			 'url': '/web/binary/download_template_account_account',
			 'target': 'new',
			 }