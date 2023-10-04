# -*- coding: utf-8 -*-

import time
from datetime import datetime
import tempfile
import binascii
import xlrd
from datetime import date, datetime
from odoo.exceptions import UserError
from odoo import models, fields, api, _

class ImportJournalEntryIt(models.Model):
	_name = 'import.journal.entry.it'

	name = fields.Char(string=u'Nombre')
	document_file = fields.Binary(string='Excel')
	name_file = fields.Char(string='Nombre de Archivo')
	type = fields.Selection([('out_invoice','Factura Cliente'),
	('in_invoice','Factura Proveedor'),
	('out_refund','Factura Rectificativa Cliente'),
	('in_refund','Factura Rectificativa Proveedor'),
	('entry','Asiento Contable')],default='out_invoice',string='Tipo')
	ref = fields.Char(string='Referencia')
	state = fields.Selection([('draft','Borrador'),('import','Importado'),('cancel','Cancelado')],string='Estado',default='draft')
	move_ids = fields.One2many('account.move', 'import_journal_entry_it_id', string='Asientos')
	company_id = fields.Many2one('res.company',string=u'Compañía',default=lambda self: self.env.company)

	@api.model
	def create(self,vals):
		id_seq = self.env['ir.sequence'].search([('name','=','Importaciones Asientos Contables'),('company_id','=',self.env.company.id)], limit=1)
		if not id_seq:
			if not id_seq:
				id_seq = self.env['ir.sequence'].create({'name':'Importaciones Asientos Contables',
				'implementation':'no_gap',
				'active':True,
				'prefix':'IMP-',
				'padding':5,
				'number_increment':1,
				'number_next_actual' :1,
				'company_id':self.env.company.id})

		vals['name'] = id_seq._next()
		t = super(ImportJournalEntryIt,self).create(vals)
		return t
	
	def open_entries(self):
		self.ensure_one()
		action = self.env.ref('account.action_move_journal_line').read()[0]
		domain = [('id', 'in', self.move_ids.ids)]
		context = dict(self.env.context, default_invoice_id=self.id)
		views = [(self.env.ref('account.view_move_tree').id, 'tree'), (False, 'form'), (False, 'kanban')]
		return dict(action, domain=domain, context=context, views=views)

	def importar(self):
		if not self.document_file:
			raise UserError('Tiene que cargar un archivo.')
		
		try:
			fp = tempfile.NamedTemporaryFile(delete= False,suffix=".xlsx")
			fp.write(binascii.a2b_base64(self.document_file))
			fp.seek(0)
			workbook = xlrd.open_workbook(fp.name)
			sheet = workbook.sheet_by_index(0)
			move_ids = []
		except:
			raise UserError("Archivo invalido!")

		for row_no in range(sheet.nrows):
			if row_no <= 0:
				continue
			else:
				line = list(map(lambda row:isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
				if len(line) == 29:
					date_string = None
					invoice_date_string = None
					date_maturity_string = None
					date_invoice_it_string = None
					if line[3] != '':
						a1 = int(float(line[3]))
						a1_as_datetime = datetime(*xlrd.xldate_as_tuple(a1, workbook.datemode))
						date_string = a1_as_datetime.date().strftime('%Y-%m-%d')
					if line[4] != '':
						a2 = int(float(line[4]))
						a2_as_datetime = datetime(*xlrd.xldate_as_tuple(a2, workbook.datemode))
						invoice_date_string = a2_as_datetime.date().strftime('%Y-%m-%d')
					
					if line[21] != '':
						a3 = int(float(line[21]))
						a3_as_datetime = datetime(*xlrd.xldate_as_tuple(a3, workbook.datemode))
						date_maturity_string = a3_as_datetime.date().strftime('%Y-%m-%d')

					if line[27] != '':
						a4 = int(float(line[27]))
						a4_as_datetime = datetime(*xlrd.xldate_as_tuple(a4, workbook.datemode))
						date_invoice_it_string = a4_as_datetime.date().strftime('%Y-%m-%d')
					values = ({'number':line[0],
								'type_document_id':line[1],
								'ref': line[2],
								'date': date_string,
								'invoice_date':invoice_date_string,
								'partner_id':line[5],
								'journal_id': line[6],
								'glosa': line[7],
								'currency_id_am':line[8] if line[8] else 'PEN',
								'tc':line[9] if line[9] else '1',
								'amount_mn':line[10] if line[10] != '' else 0,
								'amount_me':line[11] if line[11] != '' else 0,
								'account_id':line[12],
								'td_aml':line[13],
								'partner_id_aml':line[14],
								'debit':line[15],
								'credit':line[16],
								'currency_id_aml':line[17] if line[17] else 'PEN',
								'amount_currency':line[18],
								'tc_aml':line[19],
								'nro_comp':line[20],
								'date_maturity':date_maturity_string,
								'name':line[22],
								'analytic_account_id':line[23],
								'tag_ids':line[24],
								'amount_tax':line[25],
								'amount_tax_me':line[26],
								'invoice_date_it':date_invoice_it_string,
								'cta_cte':line[28] == 'SI',
								})
				elif len(line) > 27:
					raise UserError('Tu archivo tiene columnas mas columnas de lo esperado.')
				else:
					raise UserError('Tu archivo tiene columnas menos columnas de lo esperado.')
				date_invoice_it_string
				res = self.make_move(values)
				move_ids.append(res)

		for res in move_ids: 
			if res.state in ['draft']:
				res.post()
			res.write({'move_type': self.type})
		self.state = 'import'
	
	def action_cancel(self):
		for move in self.move_ids:
			move.button_cancel()
			move.line_ids.unlink()
			move.name = "/"
			move.unlink()

		self.state = 'cancel'

	def action_draft(self):
		self.state = 'draft'

	def make_move(self, values):
		move_obj = self.env['account.move']

		
		if str(values.get('journal_id')) == '':
			raise UserError('El campo "journal_id" no puede estar vacio.')
		
		s = str(values.get("journal_id"))
		code = s.rstrip('0').rstrip('.') if '.' in s else s
		journal_id = self.find_journal(code)
		
		if self.type != 'entry':
			if str(values.get('ref')) == '':
				raise UserError('El campo "ref" no puede estar vacio.')
			if str(values.get('type_document_id')) == '':
				raise UserError('El campo "type_document_id" no puede estar vacio.')
			if str(values.get('partner_id')) == '':
				raise UserError('El campo "partner_id" no puede estar vacio.')
		
		partner_id = l10n_latam_document_type_id = None
		if str(values.get('partner_id')) != '':
			s = str(values.get("partner_id"))
			vat = s.rstrip('0').rstrip('.') if '.' in s else s
			partner_id = self.find_partner(vat)

		if str(values.get('type_document_id')) != '':
			s = str(values.get("type_document_id"))
			code = s.rstrip('0').rstrip('.') if '.' in s else s
			l10n_latam_document_type_id = self.find_type_document(code)

		move_search = move_obj.search([
					('ref', '=', values.get('ref')),
					('name', '=', values.get('number')),
					('move_type', '=', 'entry'),
					('journal_id','=',journal_id.id),
					('company_id','=',self.company_id.id)
				],limit=1)

		if move_search:
			if move_search.date.strftime('%Y-%m-%d') != values.get('date'):
				raise UserError(_('La Fecha Contable "%s" es diferente al elegido en la cabecera de la primera linea.\n Por favor define la misma.') % values.get('date'))

			if move_search.glosa != values.get('glosa'):
				raise UserError(_('La glosa "%s" es diferente al elegido en la cabecera de la primera linea.\n Por favor define la misma.') % values.get('glosa'))

			if move_search.invoice_date.strftime('%Y-%m-%d')  != values.get('invoice_date'):
				raise UserError(_('La Fecha Factura "%s" es diferente al elegido en la cabecera de la primera linea.\n Por favor define la misma.') % values.get('invoice_date'))

			if move_search.currency_id.name != values.get('currency_id_am'):
				raise UserError(_('La moneda "%s" es diferente al elegido en la cabecera de la primera linea.\n Por favor define la misma.') % values.get('currency_id_am'))

			if ('%.4f' % move_search.currency_rate != '%.4f' % float(values.get('tc')) and move_search.currency_id.name == 'USD'):
				raise UserError(_('El tipo de Cambio "%s" es diferente al elegido en la cabecera de la primera linea.\n Por favor define el mismo.') % values.get('tc'))

			self.make_move_line(values, move_search)
			return move_search

		else:
			currency = self.env['res.currency'].search([('name','=',values.get("currency_id_am"))],limit=1)
			move_id = move_obj.create({
				'date':values.get('date'),
				'partner_id' : partner_id.id if partner_id else None,
				'currency_id' : currency.id,
				'move_type' : 'entry',
				'invoice_date':values.get('invoice_date'),
				'invoice_date_due':values.get('date_maturity'),
				'journal_id' : journal_id.id,
				'l10n_latam_document_type_id' : l10n_latam_document_type_id.id if l10n_latam_document_type_id else None,
				'ref' : str(values.get('ref')),
				'currency_rate' : float(values.get("tc")) if values.get("tc") else 1,
				'glosa': str(values.get('glosa')),
				'amount_total':float(values.get('amount_me')) if currency.name != 'PEN' else values.get('amount_mn'),
				'amount_total_signed':float(values.get('amount_mn')),
				'company_id' : self.company_id.id
			})
			self.make_move_line(values, move_id)
			move_id.write({'name':values.get('number')})
			return move_id

	def make_move_line(self,values,move_id):
		if values.get("account_id") == "":
			raise UserError(_('El campo de account_id no puede estar vacío.') )

		analytic_account_id = None

		if values.get("analytic_account_id"):
			analytic_account_id = self.find_analytic_account(values.get("analytic_account_id"))

		partner_id = type_document_id = None
		if values.get("partner_id_aml") != "":
			s = str(values.get("partner_id_aml"))
			vat = s.rstrip('0').rstrip('.') if '.' in s else s
			partner_id = self.find_partner(vat)

		if values.get("td_aml") != "":
			s = str(values.get("td_aml"))
			code = s.rstrip('0').rstrip('.') if '.' in s else s
			type_document_id = self.find_type_document(code)

		account_id = self.find_account(values.get("account_id"))

		tag_ids = []

		if values.get('tag_ids'):
			tag_names = values.get('tag_ids').split(',')
			for name in tag_names:
				tag = self.env['account.account.tag'].search([('name', '=', name)])
				if not tag:
					raise UserError(_(' No existe la Etiqueta de Cuenta "%s".') % name)
				tag_ids.append(tag.id)

		currency = self.env['res.currency'].search([('name','=',values.get("currency_id_aml"))],limit=1)
		if currency.name != 'PEN':
			vals = {
				'account_id': account_id.id if account_id else None,
				'partner_id': partner_id.id if partner_id else None,
				'type_document_id':type_document_id.id if type_document_id else None,
				'nro_comp': values.get("nro_comp"),
				'name': values.get("name"),
				'currency_id': currency.id,
				'amount_currency': float(values.get("amount_currency")) if values.get("amount_currency") else 0,
				'debit': float(values.get("debit")) if values.get("debit") else 0,
				'credit': float(values.get("credit")) if values.get("credit") else 0,
				'date_maturity':values.get("date_maturity"),
				'invoice_date_it':values.get("invoice_date_it"),
				'cta_cte_origen':values.get("cta_cte"),
				'company_id': self.company_id.id,
				'tc': values.get("tc_aml") if values.get("tc_aml") else 1,
				'analytic_account_id': analytic_account_id.id if analytic_account_id else None,
				'tax_amount_it': float(values.get("amount_tax")) if values.get("amount_tax") else 0,
				'tax_amount_me': float(values.get("amount_tax_me")) if values.get("amount_tax_me") else 0,
				'tax_tag_ids':([(6,0,tag_ids)]),
			}
		else:
			vals = {
				'account_id': account_id.id if account_id else None,
				'partner_id': partner_id.id if partner_id else None,
				'type_document_id':type_document_id.id if type_document_id else None,
				'nro_comp': values.get("nro_comp"),
				'name': values.get("name"),
				'debit': float(values.get("debit")) if values.get("debit") else 0,
				'credit': float(values.get("credit")) if values.get("credit") else 0,
				'date_maturity':values.get("date_maturity"),
				'invoice_date_it':values.get("invoice_date_it"),
				'cta_cte_origen':values.get("cta_cte"),
				'company_id': self.company_id.id,
				'analytic_account_id': analytic_account_id.id if analytic_account_id else None,
				'tax_amount_it': float(values.get("amount_tax")) if values.get("amount_tax") else 0,
				'tax_amount_me': float(values.get("amount_tax_me")) if values.get("amount_tax_me") else 0,
				'tax_tag_ids':([(6,0,tag_ids)])
			}

		move_id.with_context(check_move_validity=False).write({'line_ids' :([(0,0,vals)]) })
		move_id.write({'import_journal_entry_it_id': self.id})
		
		return move_id

	def find_partner(self, name):
		partner_obj = self.env['res.partner']
		partner_search = partner_obj.search([('vat', '=', str(name))],limit=1)
		if partner_search:
			return partner_search
		else:
			raise UserError(_('No existe un Partner con el Nro de Documento "%s"') % name)

	def find_journal(self,code):
		journal_search = self.env['account.journal'].search([('code','=',code),('company_id','=',self.company_id.id)],limit=1)
		if journal_search:
			return journal_search
		else:
			raise UserError(_('No existe el diario "%s" en la Compañia.') % code)

	def find_type_document(self,code):
		catalog_payment_search = self.env['l10n_latam.document.type'].search([('code', '=', str(code))],limit=1)
		if catalog_payment_search:
			return catalog_payment_search
		else:
			raise UserError(_('No existe un Tipo de Comprobante con el Codigo "%s"') % code)
	
	def find_analytic_account(self, code):
		analytic_obj = self.env['account.analytic.account']
		analytic_search = analytic_obj.search([('code', '=', str(code)),('company_id','=',self.company_id.id)],limit=1)
		if analytic_search:
			return analytic_search
		else:
			raise UserError(_('No existe una Cuenta Analitica con el Codigo "%s" en esta Compañia') % code)

	def find_account(self, code):
		account_obj = self.env['account.account']
		account_search = account_obj.search([('code', '=', str(code)),('company_id','=',self.company_id.id)],limit=1)
		if account_search:
			return account_search
		else:
			raise UserError(_('No existe una Cuenta con el Codigo "%s" en esta Compañia') % code)

	def download_template(self):
		return {
			 'type' : 'ir.actions.act_url',
			 'url': '/web/binary/download_template_import_journal_entry',
			 'target': 'new',
			 }