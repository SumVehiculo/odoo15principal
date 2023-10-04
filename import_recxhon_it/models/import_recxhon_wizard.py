# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import Warning , UserError
import base64
from datetime import date, datetime, timedelta

class ImportRecxhonWizard(models.Model):
	_name = 'import.recxhon.wizard'
	_description = 'Import Recxhon Wizard'	

	name = fields.Char(string=u'Nombre')
	account_id = fields.Many2one('account.account',string='Cuenta')
	journal_id = fields.Many2one('account.journal',string='Diario')
	document_file = fields.Binary(string='Archivo')
	name_file = fields.Char(string='Nombre de Archivo')
	state = fields.Selection([('draft','Borrador'),('import','Importado'),('cancel','Cancelado')],string='Estado',default='draft')
	move_ids = fields.One2many('account.move','import_recxhon_id',string='Facturas')
	company_id = fields.Many2one('res.company',string=u'Compañía',default=lambda self: self.env.company)

	@api.model
	def create(self,vals):
		id_seq = self.env['ir.sequence'].search([('name','=','Importaciones Rec x Hon')], limit=1)
		if not id_seq:
			if not id_seq:
				id_seq = self.env['ir.sequence'].create({'name':'Importaciones Rec x Hon',
				'implementation':'no_gap','active':True,'prefix':'IRXH-','padding':5,'number_increment':1,'number_next_actual' :1})

		vals['name'] = id_seq._next()
		t = super(ImportRecxhonWizard,self).create(vals)
		return t
	
	def unlink(self):
		if self.state != 'draft':
			raise UserError('No se puede eliminar una importacion en proceso.')
		t = super(ImportRecxhonWizard,self).unlink()
		return t

	def import_invoices(self):
		self.ensure_one()
		if self.document_file:
			if not self.account_id:
				raise UserError('Se necesita de una cuenta para crear las facturas')
			if not self.journal_id:
				raise UserError('Se necesita de un diario para crear las facturas')
			file_content = base64.decodestring(self.document_file)
			file_content = file_content.decode("utf-8")
			process_file = file_content.split("\r\n")
			invoice_obj = self.env['account.move']
			for i in range(len(process_file)-1):
				if i==0:
					continue
				else:
					data = process_file[i].split('|')
					try:
						if data[3] == 'NO ANULADO':
							partner_id = self.find_partner(data[5] if data[5] else '')
							currency_id = self.find_currency('PEN' if data[11] == 'SOLES' else 'USD')
							salesperson_id = self.env.uid
							inv_date = datetime.strptime(data[0],'%d/%m/%Y').date()
							type_document_id = self.find_type_document('02')

							inv_id = invoice_obj.create({
								'name': '/',
								'partner_id' : partner_id.id,
								'currency_id' : currency_id.id,
								'invoice_user_id':salesperson_id,
								'move_type' : 'in_invoice',
								'date':inv_date,
								'invoice_date':inv_date,
								'journal_id' : self.journal_id.id,
								'l10n_latam_document_type_id' : type_document_id.id,
								'ref' : data[2] if data[2] else '',
								'glosa': data[9] if data[9] else '',
								'company_id' : self.env.company.id
							})

							tax_ids = []
							tax_name = '4TA0%' if float(data[13]) == 0 else '4TA8%'
							tax = self.env['account.tax'].search([('name', '=', tax_name), ('type_tax_use', '=', 'purchase')],limit=1)
							if not tax:
								raise Warning('"%s" Tax not in your system' % tax_name)
							tax_ids.append(tax.id)

							product_uom = self.env['uom.uom'].search([('name', '=', 'Unidades')],limit=1)
							if not product_uom:
								raise Warning(' "Unidades" Product UOM category is not available.')

							vals = {
								'quantity' : 1,
								'price_unit' :data[12] if data[12] else 1,
								'discount':0,
								'name' : data[9] if data[9] else '',
								'account_id' : self.account_id.id,
								'product_uom_id' : product_uom.id,
								'company_id' : self.env.company.id
							}
							if tax_ids:
								vals.update({'tax_ids':([(6,0,tax_ids)])})

							inv_id.write({'invoice_line_ids' :([(0,0,vals)]), 'import_recxhon_id': self.id, 'l10n_latam_document_type_id': type_document_id.id })
							inv_id._get_ref()
							inv_id._get_currency_rate()
							inv_id._compute_amount()
							inv_id.flush()

					except Exception as e:
						raise UserError(e)		
		self.state = 'import'	

	def action_cancel(self):
		for move in self.move_ids:
			move.button_cancel()
			move.line_ids.unlink()
			move.name = False
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
		domain = [('id', 'in', self.move_ids.line_ids.ids)]
		context = dict(self.env.context, default_invoice_id=self.id)
		views = [(self.env.ref('account.view_move_line_tree').id, 'tree'), (False, 'form'), (False, 'kanban')]
		return dict(action, domain=domain, context=context, views=views)		

	def find_currency(self, name):
		currency_obj = self.env['res.currency']
		currency_search = currency_obj.search([('name', '=', name)],limit=1)
		if currency_search:
			return currency_search
		else:
			raise Warning(_(' "%s" Currency are not available.') % name)

	def find_partner(self, name):
		partner_obj = self.env['res.partner']
		partner_search = partner_obj.search([('vat', '=', str(name))],limit=1)
		if partner_search:
			return partner_search
		else:
			raise Warning(_('No existe un Partner con el Nro de Documento "%s"') % name)

	def find_type_document(self,name):
		type_document_search = self.env['l10n_latam.document.type'].search([('code','=',str(name))],limit=1)
		if type_document_search:
			return type_document_search
		else:
			raise Warning(_('No existe un Tipo de Comprobante con el Codigo"%s"') % name)