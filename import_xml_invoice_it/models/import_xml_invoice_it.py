# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, RedirectWarning, UserError
import base64
from lxml import etree
from datetime import *

class ImportXmlInvoiceIt(models.Model):
	_name = 'import.xml.invoice.it'
	_description = 'Import Xml Invoice It'

	name = fields.Char(string=u'Nombre')
	date = fields.Date(string=u'Fecha Importación')
	move_ids = fields.One2many('account.move', 'xml_import_code', string='Asientos')
	move_line_ids = fields.One2many('account.move.line', 'xml_import_code', string='Lineas')
	company_id = fields.Many2one('res.company',string=u'Compañía',default=lambda self: self.env.company)
	lineas = fields.Many2many('ir.attachment', string='Archivos')
	type = fields.Selection([('in_invoice','Factura Proveedor'),('out_invoice','Factura Cliente'),('in_refund','Rectificativa Proveedor'),('out_refund','Rectificativa Cliente')],string='Tipo',default='in_invoice')
	journal_id = fields.Many2one('account.journal',string='Diario')
	expense_account_id = fields.Many2one('account.account',string='Cuenta de Gastos')
	income_account_id = fields.Many2one('account.account',string='Cuenta de Ingresos')
	state = fields.Selection([('draft','Borrador'),('import','Importado'),('cancel','Cancelado')],string='Estado',default='draft')

	@api.model
	def create(self,vals):
		id_seq = self.env['ir.sequence'].search([('name','=','Importaciones XML Facturas')], limit=1)
		if not id_seq:
			if not id_seq:
				id_seq = self.env['ir.sequence'].create({'name':'Importaciones XML Facturas','implementation':'no_gap','active':True,'prefix':'IXML-','padding':5,'number_increment':1,'number_next_actual' :1})

		vals['name'] = id_seq._next()
		t = super(ImportXmlInvoiceIt,self).create(vals)
		return t
	
	def unlink(self):
		if self.state != 'draft':
			raise UserError('No se puede eliminar una importacion en proceso.')
		t = super(ImportXmlInvoiceIt,self).unlink()
		return t

	def import_file(self):
		def _get_attachment_content(attachment):
			return hasattr(attachment, 'content') and getattr(attachment, 'content') or base64.b64decode(attachment.datas)

		import os
		import zipfile

		if not self.lineas:
			raise UserError(u'Es necesario cargar archivos.')
		if not self.journal_id:
			raise UserError(u'Falta establecer "Diario"')
		if not self.expense_account_id and self.type in ['in_invoice','in_refund']:
			raise UserError(u'Falta establecer "Cuenta de Gastos"')
		if not self.income_account_id and self.type in ['out_invoice','out_refund']:
			raise UserError(u'Falta establecer "Cuenta de Ingresos"')

		for elem in self.lineas:               
			content = _get_attachment_content(elem)
			filename = elem.name
			def get_value(target_tree, xpath, namespaces):
				try:
					return target_tree.xpath(xpath, namespaces=namespaces)[0].text
				except IndexError as e:
					print(e)
					return ""
					
			if not filename.upper().endswith('.XML'):
				raise ValidationError('Wrong file format.')

			invoice = self.env['account.move'].create({
				'move_type' : self.type,
				'journal_id' : self.journal_id.id,
				'glosa': 'Importacion Facturas',
				'xml_import_code': self.id,
				'currency_id':self.env.company.currency_id.id,
				'company_id' : self.env.company.id})

			type_invoice = invoice.move_type

			Issue_Date = False
			Sender_ID = False
			Currency_ID = False
			OrderReference = False
			Invoice_ID = False
			Tax_Amount_Total = False
			DueDate = False

			is_supplier = False
			is_customer = False
			supplier_rank = 0
			customer_rank = 0

			for line in invoice.invoice_line_ids:
				line.unlink()
			try:
				tree = etree.fromstring(content)
				type_import = "Invoice" if self.type in ('in_invoice','out_invoice') else "CreditNote"

				ns = {"cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
						"cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
						"i2": "urn:oasis:names:specification:ubl:schema:xsd:%s-2"%(type_import)}
				cabecera = True
				if self.type in ('in_invoice','out_invoice'):
					for x in tree.xpath("//cac:InvoiceLine", namespaces=ns):
						if cabecera:
							Issue_Date = get_value(x, "../cbc:IssueDate", ns)
							DueDate = get_value(x, "../cbc:DueDate", ns)
							Invoice_ID = get_value(x, "../cbc:ID", ns)
							OrderReference = get_value(x, "../cac:OrderReference/cbc:ID", ns)
							TypeDocument = get_value(x, "../cbc:InvoiceTypeCode", ns)
							Currency_Name = get_value(x, "../cbc:DocumentCurrencyCode", ns)
							Sender_ID = get_value(x, "../cac:AccountingCustomerParty/cbc:CustomerAssignedAccountID", ns) or get_value(x, "../cac:AccountingCustomerParty/cac:Party/cac:PartyIdentification/cbc:ID", ns)
							Receiver_ID = get_value(x, "../cac:AccountingSupplierParty/cbc:SupplierAssignedAccountID", ns) or get_value(x, "../cac:AccountingSupplierParty/cac:Party/cac:PartyIdentification/cbc:ID", ns)
							Tax_Amount_Total = get_value(x, "../cac:TaxTotal/cbc:TaxAmount", ns)
							Partner_Name = get_value(x, "../cac:AccountingCustomerParty/cac:Party/cac:PartyName/cbc:Name", ns) or get_value(x, "../cac:AccountingCustomerParty/cac:Party/cac:PartyLegalEntity/cbc:RegistrationName", ns)
							Supplier_Name = get_value(x, "../cac:AccountingSupplierParty/cac:Party/cac:PartyName/cbc:Name", ns) or get_value(x, "../cac:AccountingSupplierParty/cac:Party/cac:PartyLegalEntity/cbc:RegistrationName", ns)
							if type_invoice == 'in_invoice':
								Sender_ID = Receiver_ID
								Partner_Name = Supplier_Name
								supplier_rank = 1
								is_supplier = True
							else:
								customer_rank = 1
								is_customer = True
							cabecera = False
						Currency_ID = self.env['res.currency'].search([('name', 'ilike', Currency_Name)], limit=1)
						TypeDocumentID = self.env['l10n_latam.document.type'].search([('code', '=', TypeDocument)], limit=1)

						Product_Name = get_value(x, "cac:Item/cbc:Description", ns)
						Line_Quantity = get_value(x, "cbc:InvoicedQuantity", ns)
						Price_Unit = get_value(x, "cac:Price/cbc:PriceAmount", ns)
						tax_ids = []
						for t in tree.xpath("//cac:TaxTotal/cac:TaxSubtotal", namespaces=ns):
							Tax_Name = get_value(t, "cac:TaxCategory/cac:TaxScheme/cbc:ID", ns)
							tax_type = 'sale'
							if type_invoice == 'in_invoice':
								tax_type = 'purchase'
							Tax_Line_ID = self.env['account.tax'].search([('code_fe', '=', Tax_Name),('type_tax_use','=',tax_type),('company_id','=',self.env.company.id)], limit=1)
							if Tax_Line_ID.id:
								tax_ids.append(Tax_Line_ID.id)

						tem = invoice.env['res.partner'].search([('vat', '=', Sender_ID )], limit=1)
						if len(tem) == 0:
							is_company = True
							if len(Sender_ID)==8:
								is_company = False
							else:
								if Sender_ID[:2] != '20':
									is_company = False
							vals = {
								'name': Partner_Name,
								'vat': Sender_ID,
								'l10n_latam_identification_type_id': self.env['l10n_latam.identification.type'].search([('name','=','DNI')],limit=1).id if len(Sender_ID)==8 else self.env['l10n_latam.identification.type'].search(['|',('name','=','VAT'),('name','=','RUC')],limit=1).id,
								'is_company':is_company,
								'supplier_rank':supplier_rank,
								'is_supplier':is_supplier,
								'customer_rank':customer_rank,
								'is_customer':is_customer,
							}
							self.env['res.partner'].create(vals)
						invoice.partner_id = invoice.env['res.partner'].search([('vat', '=', Sender_ID )], limit=1)
						invoice.currency_id = Currency_ID.id
						invoice.date = Issue_Date
						invoice.invoice_date = Issue_Date
						invoice.invoice_date_due = DueDate
						cuentaL = False
						if self.type in ('out_invoice'):
							cuentaL = self.income_account_id.id
						else:
							cuentaL = self.expense_account_id.id
						invoice._get_currency_rate()
						vals = {
							'name': Product_Name,
							'quantity': float(Line_Quantity),
							'price_unit': float(Price_Unit),
							'tax_ids': [(6, 0, tax_ids)],
							'account_id': cuentaL,
							'discount':0,
							'xml_import_code': self.id,
							'company_id':self.env.company.id
						}
						invoice.write({'invoice_line_ids' :([(0,0,vals)]) })
						for i in invoice.invoice_line_ids:
							i._onchange_price_subtotal()
				else:
					if tree.xpath("//cac:CreditNoteLine", namespaces=ns):
						for x in tree.xpath("//cac:CreditNoteLine", namespaces=ns):
							if cabecera:
								Issue_Date = get_value(x, "../cbc:IssueDate", ns)
								DueDate = get_value(x, "../cbc:DueDate", ns)
								Invoice_ID = get_value(x, "../cbc:ID", ns)
								OrderReference = get_value(x, "../cac:InvoiceDocumentReference/cbc:ID", ns)
								TypeDocumentReference = get_value(x, "//cac:InvoiceDocumentReference/cbc:DocumentTypeCode", ns)
								DateReference = get_value(x, "//cac:InvoiceDocumentReference/cbc:IssueDate", ns)
								TypeDocument = get_value(x, "../cbc:InvoiceTypeCode", ns)
								Currency_Name = get_value(x, "../cbc:DocumentCurrencyCode", ns)
								Sender_ID = get_value(x, "../cac:AccountingCustomerParty/cbc:CustomerAssignedAccountID", ns) or get_value(x, "../cac:AccountingCustomerParty/cac:Party/cac:PartyIdentification/cbc:ID", ns)
								Receiver_ID = get_value(x, "../cac:AccountingSupplierParty/cbc:SupplierAssignedAccountID", ns) or get_value(x, "../cac:AccountingSupplierParty/cac:Party/cac:PartyIdentification/cbc:ID", ns)
								Tax_Amount_Total = get_value(x, "../cac:TaxTotal/cbc:TaxAmount", ns)
								Partner_Name = get_value(x, "../cac:AccountingCustomerParty/cac:Party/cac:PartyName/cbc:Name", ns) or get_value(x, "../cac:AccountingCustomerParty/cac:Party/cac:PartyLegalEntity/cbc:RegistrationName", ns)
								Supplier_Name = get_value(x, "../cac:AccountingSupplierParty/cac:Party/cac:PartyName/cbc:Name", ns) or get_value(x, "../cac:AccountingSupplierParty/cac:Party/cac:PartyLegalEntity/cbc:RegistrationName", ns)
								if type_invoice == 'in_refund':
									Sender_ID = Receiver_ID
									Partner_Name = Supplier_Name
									supplier_rank = 1
									is_supplier = True
								else:
									customer_rank = 1
									is_customer = True
								cabecera = False
							Currency_ID = self.env['res.currency'].search([('name', 'ilike', Currency_Name)], limit=1)
							TypeDocumentID = self.env['l10n_latam.document.type'].search([('code', '=', TypeDocument)], limit=1)

							TypeDocumentReferenceID = self.env['l10n_latam.document.type'].search([('code', '=', TypeDocumentReference)], limit=1)
							DateReference = get_value(x, "//cac:InvoiceDocumentReference/cbc:IssueDate", ns)
							Product_Name = get_value(x, "cac:Item/cbc:Description", ns)
							Line_Quantity = get_value(x, "cbc:CreditedQuantity", ns)
							Price_Unit = get_value(x, "cac:Price/cbc:PriceAmount", ns)
							tax_ids = []
							for t in tree.xpath("//cac:TaxTotal/cac:TaxSubtotal", namespaces=ns):
								Tax_Name = get_value(t, "cac:TaxCategory/cac:TaxScheme/cbc:ID", ns)
								tax_type = 'sale'
								if type_invoice == 'in_refund':
									tax_type = 'purchase'
								Tax_Line_ID = self.env['account.tax'].search([('code_fe', '=', Tax_Name),('type_tax_use','=',tax_type),('company_id','=',self.env.company.id)], limit=1)
								if Tax_Line_ID.id:
									tax_ids.append(Tax_Line_ID.id)
						
							tem = invoice.env['res.partner'].search([('vat', '=', Sender_ID )], limit=1)
							if not tem:
								raise UserError('No existe el Socio con el RUC/DNI %s'%(Sender_ID))
							invoice.partner_id = tem.id
							invoice.currency_id = Currency_ID.id
							invoice.date = Issue_Date
							invoice.invoice_date = Issue_Date
							invoice.invoice_date_due = DueDate
							cuentaL = False
							if self.type in ('out_refund'):
								cuentaL = self.income_account_id.id
							else:
								cuentaL = self.expense_account_id.id
							invoice._get_currency_rate()
							vals = {
								'name': Product_Name,
								'quantity': float(Line_Quantity),
								'price_unit': float(Price_Unit),
								'tax_ids': [(6, 0, tax_ids)],
								'account_id': cuentaL,
								'discount':0,
								'xml_import_code': self.id,
								'company_id':self.env.company.id,
								'currency_id':Currency_ID.id if Currency_ID.name != self.env.company.currency_id.name else None,
							}
							invoice.write({'invoice_line_ids' :([(0,0,vals)]) })
							for i in invoice.invoice_line_ids:
								i._onchange_currency()
					else:
						#EN EL CASO DE QUE NO HAYA LINEAS QUIERE DECIR QUE ES UNA RETENCION ENTONCES...
						for x in tree.xpath("//cac:BillingReference", namespaces=ns):

							#raise UserError(str(x))
							if cabecera:
								Issue_Date = get_value(x, "../cbc:IssueDate", ns)
								DueDate = get_value(x, "../cbc:DueDate", ns)
								Invoice_ID = get_value(x, "../cbc:ID", ns)
								OrderReference = get_value(x, "//cac:InvoiceDocumentReference/cbc:ID", ns)
								TypeDocumentReference = get_value(x, "//cac:InvoiceDocumentReference/cbc:DocumentTypeCode", ns)
								DateReference = get_value(x, "//cac:InvoiceDocumentReference/cbc:IssueDate", ns)
								TypeDocument = get_value(x, "../cbc:InvoiceTypeCode", ns)
								Currency_Name = get_value(x, "../cbc:DocumentCurrencyCode", ns)
								Sender_ID = get_value(x, "../cac:AccountingCustomerParty/cbc:CustomerAssignedAccountID", ns) or get_value(x, "../cac:AccountingCustomerParty/cac:Party/cac:PartyIdentification/cbc:ID", ns)
								Receiver_ID = get_value(x, "../cac:AccountingSupplierParty/cbc:SupplierAssignedAccountID", ns) or get_value(x, "../cac:AccountingSupplierParty/cac:Party/cac:PartyIdentification/cbc:ID", ns)
								Tax_Amount_Total = get_value(x, "../cac:TaxTotal/cbc:TaxAmount", ns)
								Partner_Name = get_value(x, "../cac:AccountingCustomerParty/cac:Party/cac:PartyName/cbc:Name", ns) or get_value(x, "../cac:AccountingCustomerParty/cac:Party/cac:PartyLegalEntity/cbc:RegistrationName", ns)
								Supplier_Name = get_value(x, "../cac:AccountingSupplierParty/cac:Party/cac:PartyName/cbc:Name", ns) or get_value(x, "../cac:AccountingSupplierParty/cac:Party/cac:PartyLegalEntity/cbc:RegistrationName", ns)
								if type_invoice == 'in_refund':
									Sender_ID = Receiver_ID
									Partner_Name = Supplier_Name
									supplier_rank = 1
									is_supplier = True
								else:
									customer_rank = 1
									is_customer = True
								cabecera = False
							
							Currency_ID = self.env['res.currency'].search([('name', 'ilike', Currency_Name)], limit=1)
							TypeDocumentID = self.env['l10n_latam.document.type'].search([('code', '=', TypeDocument)], limit=1)
							#raise UserError(TypeDocumentReference)
							TypeDocumentReferenceID = self.env['l10n_latam.document.type'].search([('code', '=', TypeDocumentReference)], limit=1)
							DateReference = get_value(x, "//cac:InvoiceDocumentReference/cbc:IssueDate", ns)
							Product_Name = get_value(x, "cac:Item/cbc:Description", ns)
							Line_Quantity = get_value(x, "cbc:CreditedQuantity", ns) if get_value(x, "cbc:CreditedQuantity", ns) else 1
							Price_Unit = get_value(x, "cac:Price/cbc:PriceAmount", ns)
							tax_ids = []
							for t in tree.xpath("//cac:TaxTotal/cac:TaxSubtotal", namespaces=ns):
								Tax_Name = get_value(t, "cac:TaxCategory/cac:TaxScheme/cbc:ID", ns)
								tax_type = 'sale'
								if type_invoice == 'in_refund':
									tax_type = 'purchase'
								Tax_Line_ID = self.env['account.tax'].search([('code_fe', '=', Tax_Name),('type_tax_use','=',tax_type),('company_id','=',self.env.company.id)], limit=1)
								if Tax_Line_ID.id:
									tax_ids.append(Tax_Line_ID.id)
						
							tem = invoice.env['res.partner'].search([('vat', '=', Sender_ID )], limit=1)
							if not tem:
								raise UserError('No existe el Socio con el RUC/DNI %s'%(Sender_ID))
							invoice.partner_id = tem.id
							invoice.currency_id = Currency_ID.id
							invoice.date = Issue_Date
							invoice.invoice_date = Issue_Date
							invoice.invoice_date_due = DueDate
							cuentaL = False
							if self.type in ('out_refund'):
								cuentaL = self.income_account_id.id
							else:
								cuentaL = self.expense_account_id.id
							invoice._get_currency_rate()


					fac_rel = self.env['account.move'].search([('ref','=',OrderReference),('partner_id','=',invoice.env['res.partner'].search([('vat', '=', Sender_ID )], limit=1)[0].id),('company_id','=',self.env.company.id) ])
					if fac_rel:
						self.env['doc.invoice.relac'].create({
							'type_document_id':fac_rel.type_document_id.id,
							'date':fac_rel.invoice_date,
							'nro_comprobante':OrderReference,
							'amount_currency':fac_rel.amount_total,
							'amount':fac_rel.amount_total* fac_rel.currency_rate,
							'bas_amount':fac_rel.amount_untaxed* fac_rel.currency_rate,
							'tax_amount':fac_rel.amount_total* fac_rel.currency_rate - fac_rel.amount_untaxed* fac_rel.currency_rate,
							'move_id':invoice.id,
							})
					else:
						self.env['doc.invoice.relac'].create({
							'type_document_id':TypeDocumentReferenceID.id,
							'date':datetime.strptime(DateReference, '%Y-%m-%d').date() ,
							'nro_comprobante':OrderReference,
							'amount_currency':invoice.amount_total if invoice.currency_id.name != 'PEN' else 0,
							'amount':invoice.amount_total* invoice.currency_rate if invoice.currency_id.name != 'PEN' else invoice.amount_total,
							'bas_amount':invoice.amount_untaxed* invoice.currency_rate if invoice.currency_id.name != 'PEN' else invoice.amount_untaxed,
							'tax_amount':invoice.amount_total* invoice.currency_rate - invoice.amount_untaxed* invoice.currency_rate if invoice.currency_id.name != 'PEN' else invoice.amount_total-invoice.amount_untaxed,
							'move_id':invoice.id,
							})
				
			except Exception as e:
				print(e)
				import sys, traceback
				exc_type, exc_value, exc_traceback = sys.exc_info()
				t= traceback.format_exception(exc_type, exc_value,exc_traceback)
				print(t)
				raise UserError(_(e))
				
			invoice.l10n_latam_document_type_id = TypeDocumentID.id
			invoice.ref = Invoice_ID
			invoice.currency_id = Currency_ID.id
			type = invoice.move_type or self.env.context.get('move_type', 'out_invoice')

			if type in ('in_invoice', 'in_refund'):
				payment_term_id = invoice.partner_id.property_supplier_payment_term_id.id
			else:
				payment_term_id = invoice.partner_id.property_payment_term_id.id
			
			invoice.ref = Invoice_ID
			invoice._get_ref()
			invoice.partner_shipping_id = invoice.partner_id
			invoice.invoice_payment_term_id = payment_term_id
			invoice.amount_tax = Tax_Amount_Total
			invoice.amount_total = invoice.amount_untaxed + invoice.amount_tax
			invoice._get_currency_rate()
			invoice._compute_amount()
			for line in invoice.line_ids.with_context(check_move_validity=False):
				line.partner_id = invoice.partner_id.id
				line.nro_comp = invoice.ref
				line.xml_import_code = self.id
				line.type_document_id = TypeDocumentID.id
				line.currency_id = invoice.currency_id.id if invoice.currency_id.name != self.env.company.currency_id.name else self.env.company.currency_id.id


			if type in ('in_invoice', 'in_refund'):
				invoice._check_duplicate_supplier_reference()
				invoicess = self.env['account.move'].search([('ref','=',invoice.ref),
						 ('l10n_latam_document_type_id','=',invoice.l10n_latam_document_type_id.id),
						 ('partner_id','=',invoice.partner_id.id),
						 ('id','!=',invoice.id),
						 ('move_type','=',['in_invoice', 'in_refund']),
						 ('company_id','=',self.env.company.id)])
				if invoicess:
					raise UserError(u'La factura %s ya existe.'%(invoice.ref))
			else:
				invoice._check_duplicate_customer_reference()
				invoicess = self.env['account.move'].search([('ref','=',invoice.ref),
						 ('l10n_latam_document_type_id','=',invoice.l10n_latam_document_type_id.id),
						 ('id','!=',invoice.id),
						 ('move_type','=',['out_invoice', 'out_refund']),
						 ('company_id','=',self.env.company.id)])
				if invoicess:
					raise UserError(u'La factura %s ya existe.'%(invoice.ref))

				
		self.date = fields.Date.context_today(self)
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
	
	def open_entries(self):
		self.ensure_one()
		action = self.env.ref('account.action_move_journal_line').read()[0]
		domain = [('id', 'in', self.move_ids.ids)]
		context = dict(self.env.context, default_invoice_id=self.id)
		views = [(self.env.ref('account.view_move_tree').id, 'tree'), (False, 'form'), (False, 'kanban')]
		return dict(action, domain=domain, context=context, views=views)

	def open_line_entries(self):
		self.ensure_one()
		action = self.env.ref('account.action_account_moves_all').read()[0]
		domain = [('id', 'in', self.move_line_ids.ids)]
		context = dict(self.env.context, default_invoice_id=self.id)
		views = [(self.env.ref('account.view_move_line_tree').id, 'tree'), (False, 'form'), (False, 'kanban')]
		return dict(action, domain=domain, context=context, views=views)