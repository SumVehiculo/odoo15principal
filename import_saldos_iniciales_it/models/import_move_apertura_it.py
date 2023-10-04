# -*- coding: utf-8 -*-

import time
from datetime import datetime
import tempfile
import binascii
import xlrd
from datetime import date, datetime
from odoo.exceptions import Warning, UserError
from odoo.osv import osv
from odoo import models, fields, exceptions, api, _
import logging
_logger = logging.getLogger(__name__)
import io
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

class ImportMoveAperturaIt(models.Model):
	_name = 'import.move.apertura.it'

	fecha_contable = fields.Date(string='Fecha Contable')
	account_descargo_mn = fields.Many2one('account.account',string='Cuenta de Descargo Soles')
	account_descargo_me = fields.Many2one('account.account',string='Cuenta de Descargo Dolares')
	partner_descargo = fields.Many2one('res.partner',string='Partner Descargo')
	document_descargo = fields.Char(string='Documento Descargo')
	document_file = fields.Binary(string='Excel', help="El archivo Excel debe ir con la cabecera: n_ruc, n_razonsoc, n_fecha_emision, n_fecha_vencimiento, n_vendedor, n_tipo_doc, n_numero, n_moneda, n_saldo_mn, n_saldo_me, n_cuenta, n_tipo_cambio, n_doc_origin")
	name_file = fields.Char(string='Nombre de Archivo')
	state = fields.Selection([('draft','Borrador'),('import','Importado'),('cancel','Cancelado')],string='Estado',default='draft')
	journal_id = fields.Many2one('account.journal',string='Diario')
	is_opening_close = fields.Boolean(string='Apertura/Cierre',default=False)

	detalle = fields.One2many('import.move.apertura.it.line','wizard_id','Detalle')
	tipo = fields.Selection([('out','Cliente'),('in','Proveedor')],string='Tipo')
	company_id = fields.Many2one('res.company',string=u'Compañía',default=lambda self: self.env.company)

	_rec_name = 'name_file'
	
	@api.model
	def create(self,vals):	
		if len( self.env['import.move.apertura.it'].search([('state','in',('draft','cancel')),('tipo','=',self.env.context.get('default_tipo'))])) >0:
			raise UserError('Existe otra importacion pendiente en estado Borrador o Cancelado.')
		t = super(ImportMoveAperturaIt,self).create(vals)
		t.refresh()
		return t

	def write(self,vals):
		if len( self.env['import.move.apertura.it'].search([('state','in',('draft','cancel')),('id','!=',self.id),('tipo','=',self.tipo)])) >0:
			raise UserError('Existe otra importacion pendiente en estado Borrador o Cancelado.')
		t = super(ImportMoveAperturaIt,self).write(vals)
		self.refresh()
		return t
	
	def unlink(self):
		if self.state != 'draft':
			raise UserError('No se puede eliminar una importacion en proceso.')
		for i in self.detalle:
			i.unlink()
		t = super(ImportMoveAperturaIt,self).unlink()
		return t
	
	def open_entries(self):
		self.ensure_one()
		action = self.env.ref('account.action_move_journal_line').read()[0]
		move_ids = self.env['account.move'].search([('apertura_id','=',self.id)])
		domain = [('id', 'in', move_ids.ids)]
		context = dict(self.env.context, default_invoice_id=self.id)
		views = [(self.env.ref('account.view_move_tree').id, 'tree'), (False, 'form'), (False, 'kanban')]
		return dict(action, domain=domain, context=context, views=views)

	def importar(self):
		if not self.fecha_contable:
			raise UserError('Falta establecer "Fecha Contable"')
		if not self.account_descargo_mn:
			raise UserError('Falta establecer "Cuenta de Descargo Soles"')
		if not self.account_descargo_me:
			raise UserError('Falta establecer "Cuenta de Descargo Dolares"')
		if not self.partner_descargo:
			raise UserError('Falta establecer "Partner Descargo"')
		if not self.document_descargo:
			raise UserError('Falta establecer "Documento Descargo"')
		if not self.journal_id:
			raise UserError('Falta establecer "Diario"')
		if not self.tipo:
			raise UserError('Falta establecer "Tipo"')
		if not self.document_file:
			raise UserError('Tiene que cargar un archivo.')
		
		try:
			fp = tempfile.NamedTemporaryFile(delete= False,suffix=".xlsx")
			fp.write(binascii.a2b_base64(self.document_file))
			fp.seek(0)
			workbook = xlrd.open_workbook(fp.name)
			sheet = workbook.sheet_by_index(0)

		except:
			raise UserError("Archivo invalido!")

		lineas = []

		for row_no in range(sheet.nrows):
			if row_no <= 0:
				continue
			else:
				line = list(map(lambda row:isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
				if len(line) == 13:
					date_string = None
					date_due_string = None
					if line[2] != '':
						a1 = int(float(line[2]))
						a1_as_datetime = datetime(*xlrd.xldate_as_tuple(a1, workbook.datemode))
						date_string = a1_as_datetime.date().strftime('%Y-%m-%d')
					if line[3] != '':
						a1 = int(float(line[3]))
						a1_as_datetime = datetime(*xlrd.xldate_as_tuple(a1, workbook.datemode))
						date_due_string = a1_as_datetime.date().strftime('%Y-%m-%d')
					values = (0,0,{'n_ruc': line[0],
								'n_razonsoc': line[1],
								'n_fecha_emision': date_string,
								'n_fecha_vencimiento': date_due_string,
								'n_vendedor':line[4],
								'n_tipo_doc':line[5],
								'n_numero':line[6],
								'n_moneda':line[7] if line[7] else 'PEN',
								'n_saldo_mn':line[8],
								'n_saldo_me':line[9],
								'n_cuenta':line[10],
								'n_tipo_cambio':line[11],
								'n_doc_origin':line[12] or None,
								})
				elif len(line) > 13:
					raise UserError('Tu archivo tiene columnas mas columnas de lo esperado.')
				else:
					raise UserError('Tu archivo tiene columnas menos columnas de lo esperado.')

				lineas.append(values)

		self.write({'detalle': lineas})

		self.env.cr.execute("""
			
			update import_move_apertura_it_line set

			ruc = T.v1,
			razon_social = T.v2,
			fecha_emision = T.v3::date,
			fecha_vencimiento = T.v4::date,
			vendedor = T.v5,
			tipo_doc = T.v6,
			numero = T.v7,
			moneda = T.v8,
			saldo_mn = T.v9::numeric,
			saldo_me = T.v10::numeric,
			cuenta = T.v11,
			tipo_cambio = T.v12::numeric,
			doc_origin = T.v13

			from (
			select 
			iaa.id as id,
			iaa.n_ruc as v1,
			rp1.id as v2,
			iaa.n_fecha_emision as v3,
			iaa.n_fecha_vencimiento as v4,
			ru.id as v5,
			ec.id as v6,
			iaa.n_numero as v7,
			rc.id as v8,
			iaa.n_saldo_mn as v9,
			iaa.n_saldo_me as v10,
			aa.id as v11,
			iaa.n_tipo_cambio as v12,
			iaa.n_doc_origin as v13

			from import_move_apertura_it_line iaa
			left join res_partner rp on rp.vat = iaa.n_ruc
			left join res_partner rp1 on rp1.id = rp.commercial_partner_id
			left join res_partner rpp2 on rpp2.name = iaa.n_vendedor
			left join res_users ru on ru.partner_id = rpp2.id
			left join (select * from l10n_latam_document_type where active = True) ec on ec.code = iaa.n_tipo_doc
			left join res_currency rc on rc.name = iaa.n_moneda
			left join account_account aa on aa.code = iaa.n_cuenta and aa.company_id = %d
			where iaa.wizard_id = %d ) T where T.id = import_move_apertura_it_line.id
		 """ % (self.company_id.id,self.id))

		self.env.cr.execute("""
						select ruc,
						razon_social,
						vendedor,
						n_vendedor,
						cuenta,
						n_cuenta
						from import_move_apertura_it_line
						where wizard_id = %d
			""" % (self.id))

		problemas = ""
		for i in self.env.cr.fetchall():
			if not i[1]:
				problemas += "No se encontro el partner: " + i[0] + '\n'
			if not i[4]:
				problemas += "No se encontro la cuenta : " + i[5] + '\n'
			if i[3]:
				if not i[2]:
					problemas += "No se encontro el Vendedor: " + i[3] + '\n'

		if problemas != "":
			raise UserError(problemas)

		self.env.cr.execute("""select count(n_ruc) as cont,n_ruc,n_tipo_doc,n_numero,n_cuenta from import_move_apertura_it_line  where wizard_id = %d
							group by n_ruc,n_tipo_doc,n_numero,n_cuenta
							having count(n_ruc)>1""" % (self.id))

		for i in self.env.cr.fetchall():
			problemas+= "Existen "+str(i[0]) + " lineas duplicadas con los siguientes datos: \n"
			problemas+= u"RUC: "+str(i[1]) + " \n"
			problemas+= "Tipo Documento: "+str(i[2]) + " \n"
			problemas+= "Nro Comprobante: "+str(i[3]) + " \n"
			problemas+= "Cuenta: "+str(i[4]) + " \n \n"

		if problemas != "":
			raise UserError(problemas)

		############################## CREACION DE ASIENTOS CONTABLES #######################################
		parametros = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1)
		self.env.cr.execute("""select razon_social,fecha_emision,fecha_vencimiento,vendedor,tipo_doc,numero,moneda,saldo_mn,saldo_me,cuenta,tipo_cambio,doc_origin
							from import_move_apertura_it_line where wizard_id = %s order by id """ % (str(self.id)))

		data = self.env.cr.fetchall()
		document_code = self.env['l10n_latam.document.type'].search([('code','=','00')],limit=1)
		for acc in data:
			currency = self.env['res.currency'].search([('id','=',acc[6])],limit=1)
			lineas = []
			amount_mn = 0
			if self.tipo == 'out':
				
				type_invoice = ('out_refund' if parametros.dt_national_credit_note.id == acc[4] else 'out_invoice') if parametros.dt_national_credit_note else 'out_invoice'
				amount_mn = acc[7] if type_invoice == 'out_invoice' else acc[7]*-1
				vals = (0,0,{
					'account_id': self.account_descargo_me.id if currency.name != 'PEN' else self.account_descargo_mn.id,
					'partner_id': self.partner_descargo.id,
					'type_document_id': document_code.id,
					'nro_comp': self.document_descargo,
					'name': 'SALDOS DE APERTURA',
					'currency_id': currency.id if currency.name != 'PEN' else self.company_id.currency_id.id,
					'amount_currency': acc[8]*-1 if currency.name != 'PEN' else 0,
					'debit': 0 if amount_mn > 0 else abs(amount_mn),
					'credit': amount_mn if amount_mn > 0 else 0,
					'price_subtotal':acc[8] if currency.name != 'PEN' else amount_mn,
					'price_total':acc[8] if currency.name != 'PEN' else amount_mn,
					'price_unit':acc[8] if currency.name != 'PEN' else amount_mn,
					'date_maturity':acc[2],
					'company_id': self.company_id.id,
					'tc': acc[10] if currency.name != 'PEN' else 1,
					'exclude_from_invoice_tab': False,
					'balance':amount_mn*-1,
				})
				lineas.append(vals)
				vals = (0,0,{
					'account_id': acc[9],
					'partner_id': acc[0],
					'type_document_id':acc[4],
					'nro_comp': acc[5],
					'name': 'SALDOS DE APERTURA',
					'currency_id': currency.id if currency.name != 'PEN' else self.company_id.currency_id.id,
					'amount_currency': acc[8],
					'debit': amount_mn if amount_mn > 0 else 0,
					'credit': 0 if amount_mn > 0 else abs(amount_mn),
					'price_subtotal':acc[8]*-1 if currency.name != 'PEN' else amount_mn*-1,
					'price_total':acc[8]*-1 if currency.name != 'PEN' else amount_mn*-1,
					'price_unit':acc[8]*-1 if currency.name != 'PEN' else amount_mn*-1,
					'date_maturity':acc[2],
					'company_id': self.company_id.id,
					'tc': acc[10] if currency.name != 'PEN' else 1,
					'exclude_from_invoice_tab': True,
					'balance':amount_mn,
					'amount_residual': amount_mn,
					'amount_residual_currency': acc[8] if currency.name != 'PEN' else 0,
				})
				lineas.append(vals)
			else:
				type_invoice = ('in_refund' if parametros.dt_national_credit_note.id == acc[4] else 'in_invoice') if parametros.dt_national_credit_note else 'in_invoice'
				amount_mn = acc[7] if type_invoice == 'in_invoice' else acc[7]*-1
				vals = (0,0,{
					'account_id': self.account_descargo_me.id if currency.name != 'PEN' else self.account_descargo_mn.id,
					'partner_id': self.partner_descargo.id,
					'type_document_id':document_code.id,
					'nro_comp': self.document_descargo,
					'name': 'SALDOS DE APERTURA',
					'currency_id': currency.id if currency.name != 'PEN' else self.company_id.currency_id.id,
					'amount_currency': acc[8],
					'debit': amount_mn if amount_mn > 0 else 0,
					'credit': 0 if amount_mn > 0 else abs(amount_mn),
					'price_subtotal':acc[8] if currency.name != 'PEN' else amount_mn,
					'price_total':acc[8] if currency.name != 'PEN' else amount_mn,
					'price_unit':acc[8] if currency.name != 'PEN' else amount_mn,
					'date_maturity':acc[2],
					'company_id': self.company_id.id,
					'tc': acc[10] if currency.name != 'PEN' else 1,
					'exclude_from_invoice_tab': False,
					'balance':amount_mn,
				})
				lineas.append(vals)
				vals = (0,0,{
					'account_id': acc[9],
					'partner_id': acc[0],
					'type_document_id':acc[4],
					'nro_comp': acc[5],
					'name': 'SALDOS DE APERTURA',
					'currency_id': currency.id if currency.name != 'PEN' else self.company_id.currency_id.id,
					'amount_currency': acc[8]*-1,
					'debit': 0 if amount_mn > 0 else abs(amount_mn),
					'credit': amount_mn if amount_mn > 0 else 0,
					'price_subtotal':acc[8]*-1 if currency.name != 'PEN' else amount_mn*-1,
					'price_total':acc[8]*-1 if currency.name != 'PEN' else amount_mn*-1,
					'price_unit':acc[8]*-1 if currency.name != 'PEN' else amount_mn*-1,
					'date_maturity':acc[2],
					'company_id': self.company_id.id,
					'tc': acc[10] if currency.name != 'PEN' else 1,
					'exclude_from_invoice_tab': True,
					'balance':amount_mn*-1,
					'amount_residual': amount_mn*-1,
					'amount_residual_currency': acc[8]*-1 if currency.name != 'PEN' else 0,
				})
				lineas.append(vals)

			move_id = self.env['account.move'].create({
			'partner_id': acc[0],
			'company_id': self.company_id.id,
			'journal_id': self.journal_id.id,
			'date': self.fecha_contable,
			'invoice_date': acc[1],
			'invoice_date_due':acc[2],
			'l10n_latam_document_type_id':acc[4],
			'line_ids':lineas,
			'ref': acc[5],
			'state':'draft',
			'currency_rate':acc[10] if acc[10] else 1,
			'glosa':'SALDOS DE APERTURA',
			'apertura_id':self.id,
			'currency_id':currency.id if currency.name != 'PEN' else self.company_id.currency_id.id,
			'is_opening_close':self.is_opening_close,
			'invoice_user_id':acc[3] if acc[3] else self.env.user.id,
			'payment_state': 'not_paid',
			'amount_untaxed': acc[8] if currency.name != 'PEN' else amount_mn,
			'amount_total': acc[8] if currency.name != 'PEN' else amount_mn,
			'amount_residual': acc[8] if currency.name != 'PEN' else amount_mn,
			'amount_untaxed_signed': amount_mn*-1 if self.tipo == 'in' else amount_mn,
			'amount_total_signed': amount_mn*-1 if self.tipo == 'in' else amount_mn,
			'amount_residual_signed': amount_mn*-1 if self.tipo == 'in' else amount_mn,
			'invoice_origin': acc[11],
			'move_type':type_invoice})

			move_id._get_ref()

		self.state = 'import'

	def eliminar(self):
		accounts = self.env['account.move'].search([('apertura_id','=',self.id)])
		accounts.button_cancel()
		accounts.line_ids.unlink()
		accounts.name = "/"
		accounts.unlink()

		self.env.cr.execute(""" 
			DELETE FROM import_move_apertura_it_line WHERE wizard_id = """+str(self.id)+""";
			""")

		self.state = 'cancel'

	def borrador(self):
		self.state = 'draft'

	def download_template(self):
		return {
			 'type' : 'ir.actions.act_url',
			 'url': '/web/binary/download_template_import_initial?model=import.move.apertura.it&id=%s'%(self.id),
			 'target': 'new',
			 }

class ImportMoveAperturaItLine(models.Model):
	_name = 'import.move.apertura.it.line'

	wizard_id = fields.Many2one('import.move.apertura.it','Importacion')
	ruc = fields.Char(string='RUC')
	razon_social = fields.Many2one('res.partner',string='Razon Social')
	fecha_emision = fields.Date(string='Fecha Emision')
	fecha_vencimiento = fields.Date(string='Fecha Vencimiento')
	vendedor = fields.Many2one('res.users',string='Vendedor')
	tipo_doc = fields.Many2one('l10n_latam.document.type',string='Tipo Doc.')
	numero = fields.Char(string='Numero')
	moneda = fields.Many2one('res.currency',string='Moneda')
	saldo_mn = fields.Float(string='Saldo MN')
	saldo_me = fields.Float(string='Saldo ME')
	cuenta = fields.Many2one('account.account',string='Cuenta')
	tipo_cambio = fields.Float(string='Tipo Cambio',digits=(12,4))
	doc_origin = fields.Char(string='Doc Origen')

	n_ruc = fields.Char('Campo')
	n_razonsoc = fields.Char('Campo')
	n_fecha_emision = fields.Char('Campo')
	n_fecha_vencimiento = fields.Char('Campo')
	n_vendedor = fields.Char('Campo')
	n_tipo_doc = fields.Char('Campo')
	n_numero = fields.Char('Campo')
	n_moneda = fields.Char('Campo')
	n_saldo_mn = fields.Char('Campo')
	n_saldo_me = fields.Char('Campo')
	n_cuenta = fields.Char('Campo')
	n_tipo_cambio = fields.Char('Campo',digits=(12,4))
	n_doc_origin = fields.Char('Campo')