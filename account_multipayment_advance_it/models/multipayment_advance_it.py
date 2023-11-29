# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class MultipaymentAdvanceIt(models.Model):
	_name = 'multipayment.advance.it'

	name = fields.Char(string='Nombre')
	journal_id = fields.Many2one('account.journal',string='Diario')
	payment_date = fields.Date(string='Fecha de pago')
	catalog_payment_id = fields.Many2one('einvoice.catalog.payment',string='Medio de Pago')
	payment_method_id = fields.Many2one('account.payment.method',string='Metodo de Pago')
	glosa = fields.Char(string='Glosa')
	tc = fields.Float(string='Tipo Cambio',digits=(12,3),default=1)
	invoice_ids = fields.One2many('multipayment.advance.it.line','main_id',string='Facturas')
	lines_ids = fields.One2many('multipayment.advance.it.line2','main_id',string='Lineas')
	state = fields.Selection([('draft','Borrador'),('done','Finalizado')],string='Estado',default='draft')
	asiento_id = fields.Many2one('account.move',string='Asiento Contable')
	company_id = fields.Many2one('res.company',string=u'Compañía',default=lambda self: self.env.company)

	#OTRA INFORMACION
	partner_cash_id = fields.Many2one('res.partner',string='Partner Caja')
	type_document_cash_id = fields.Many2one('l10n_latam.document.type',string='Tipo Comprobante Caja')
	nro_operation = fields.Char(string=u'Nro Operación Caja')
	cash_flow_id = fields.Many2one('account.cash.flow',string="Flujo Caja")
	move_name = fields.Char(string='Voucher Asiento')
	journal_move = fields.Many2one('account.journal',string='Diario Asiento')
	date_move = fields.Date(string='Fecha Asiento')
	amount = fields.Float(string='Monto',compute='compute_amount_cash',store=True)

	@api.depends('company_id','asiento_id')
	def compute_amount_cash(self):
		for m in self:
			amount = 0
			if m.asiento_id:
				for i in m.asiento_id.line_ids:
					amount += (i.debit - i.credit)
			
			m.amount = amount

	@api.model
	def create(self, vals):
		id_seq = self.env['ir.sequence'].search([('name', '=', 'Pagos Multiples Avanzados IT'),('company_id','=',self.env.company.id)],limit=1)

		if not id_seq:
			id_seq = self.env['ir.sequence'].create({'name': 'Pagos Multiples Avanzados IT', 'company_id': self.env.company.id, 'implementation': 'no_gap','active': True, 'prefix': 'PM-', 'padding': 6, 'number_increment': 1, 'number_next_actual': 1})

		vals['name'] = id_seq._next()
		t = super(MultipaymentAdvanceIt, self).create(vals)
		return t
	
	def write(self, vals):
		res = super(MultipaymentAdvanceIt, self).write(vals)
		for multi in self:
			if multi.asiento_id and ('partner_cash_id' in vals or 'type_document_cash_id' in vals or 'nro_operation' in vals or 'cash_flow_id' in vals):
				line_move = multi.asiento_id.line_ids.filtered(lambda l: l.account_id.id in [self.company_id.account_journal_payment_debit_account_id.id,self.company_id.account_journal_payment_credit_account_id.id])
				line_move.write({
					'partner_id': multi.partner_cash_id.id,
					'type_document_id': multi.type_document_cash_id.id,
					'nro_comp': multi.nro_operation,
					'cash_flow_id': multi.cash_flow_id.id,
				})
		return res

	def calculate_line(self):
		amount = debe = haber = 0
		for line_i in self.invoice_ids:
			line_i.flush()
			amount += line_i.debe
			amount -= line_i.haber
		
		for line_c in self.lines_ids:
			line_c.flush()
			amount += line_c.debe
			amount -= line_c.haber

		if amount <= 0:
			debe = abs(amount)
		if amount >= 0:
			haber = abs(amount)
		retention_account_id = self.journal_id.account_multipayment_id
		if self.journal_id.check_retention:
			if not retention_account_id:
				raise UserError(u'Debe configurar la Cuenta de PM en el Diario %s'%(self.journal_id.name))
			account_id = retention_account_id.id
		else:
			if amount <= 0:
				#Debe
				if self.payment_method_id:
					line_account = self.journal_id.inbound_payment_method_line_ids.filtered(lambda l: l.payment_method_id.id == self.payment_method_id.id)
					if line_account.payment_account_id:
						account_id = line_account.payment_account_id.id
					else:
						account_id = self.company_id.account_journal_payment_debit_account_id.id
					
				else:
					account_id = self.company_id.account_journal_payment_debit_account_id.id
			else:
				#Haber
				if self.payment_method_id:
					line_account = self.journal_id.outbound_payment_method_line_ids.filtered(lambda l: l.payment_method_id.id == self.payment_method_id.id)
					if line_account.payment_account_id:
						account_id = line_account.payment_account_id.id
					else:
						account_id = self.company_id.account_journal_payment_credit_account_id.id
				else:
					account_id = self.company_id.account_journal_payment_credit_account_id.id

		line = self.lines_ids.filtered(lambda l: l.account_id.id == account_id)
		line.unlink()
		
		
		val = {
			'main_id': self.id,
			'account_id': account_id,
			'currency_id': self.journal_id.currency_id.id,
			'importe_divisa': (amount/self.tc)*-1 if self.journal_id.currency_id else 0,
			'debe': debe,
			'haber': haber,
		}
		self.env['multipayment.advance.it.line2'].create(val)
	
	def autocomplete_amount(self):
		retention_precentage = self.journal_id.multipayment_precentage
		for line_i in self.invoice_ids:
			if self.journal_id.check_retention:
				if retention_precentage == 0:
					raise UserError(u'Debe configurar el procentaje de PM en el Diario %s'%(self.journal_id.name))
				line_i.importe_divisa = line_i.saldo*retention_precentage* -1
			else:
				line_i.importe_divisa = line_i.saldo * -1
			line_i._update_debit_credit()

	def get_invoices_multipayment(self):
		wizard = self.env['get.invoices.multipayment.wizard'].create({
			'multipayment_id': self.id,
			'company_id':self.company_id.id
		})
		module = __name__.split('addons.')[1].split('.')[0]
		view = self.env.ref('%s.view_get_invoices_multipayment_wizard' % module)
		return {
			'name':u'Seleccionar Facturas',
			'res_id':wizard.id,
			'view_mode': 'form',
			'res_model': 'get.invoices.multipayment.wizard',
			'view_id': view.id,
			'context': self.env.context,
			'target': 'new',
			'type': 'ir.actions.act_window',
		}
	
	def get_templates_multipayment(self):
		wizard = self.env['get.template.multipayment.wizard'].create({
			'multipayment_id': self.id,
			'company_id':self.company_id.id
		})
		module = __name__.split('addons.')[1].split('.')[0]
		view = self.env.ref('%s.view_get_template_multipayment_wizard' % module)
		return {
			'name':u'Seleccionar Plantillas',
			'res_id':wizard.id,
			'view_mode': 'form',
			'res_model': 'get.template.multipayment.wizard',
			'view_id': view.id,
			'context': self.env.context,
			'target': 'new',
			'type': 'ir.actions.act_window',
		}

	@api.onchange('payment_date')
	def on_change_payment_date(self):
		if self.payment_date:
			usd = self.env.ref('base.USD')
			divisa_line = self.env['res.currency.rate'].search([('name','=',self.payment_date),('currency_id','=',usd.id)],limit=1)
			if divisa_line:
				self.tc = divisa_line.sale_type

	@api.onchange('tc')
	def on_change_tc(self):
		if self.tc:
			for i in self.invoice_ids:
				i._update_debit_credit()
	
	def update_saldo(self):
		for inv in self.invoice_ids:
			inv.on_change_invoice_id()

	def crear_asiento(self):
		tc = self.tc or 1
		if tc == 1:
			raise UserError(u'El tipo de cambio no puede ser 1, actualice el TC para la fecha de pago.')
		self.update_saldo()
		prob, problemas = self.validate_lines()
		if prob:
			return self.env['popup.it'].get_message(problemas)
		lineas = []

		for elemnt in self.invoice_ids:
			vals = (0,0,{
				'account_id': elemnt.account_id.id,
				'partner_id':elemnt.partner_id.id,
				'type_document_id':elemnt.tipo_documento.id,
				'nro_comp': elemnt.invoice_id.nro_comp,
				'name': self.glosa,
				'currency_id': elemnt.currency_id.id,
				'amount_currency': elemnt.importe_divisa if elemnt.currency_id else 0,
				'debit': elemnt.debe,
				'credit': elemnt.haber,
				'date_maturity':elemnt.fecha_vencimiento,
				'company_id': self.company_id.id,
				'reconciled':False,
				'tc': self.tc,
			})
			lineas.append(vals)

		for i in self.lines_ids:
			vals = (0,0,{
					'account_id': i.account_id.id,
					'partner_id': i.partner_id.id if i.partner_id else (self.partner_cash_id.id if self.partner_cash_id else None),
					'type_document_id': i.type_document_id.id if i.type_document_id else (self.type_document_cash_id.id if self.type_document_cash_id else None),
					'nro_comp': i.nro_comp if i.nro_comp else self.nro_operation,
					'analytic_account_id': i.analytic_account_id.id if i.analytic_account_id else None,
					'analytic_tag_ids':([(6,0,[i.analytic_tag_id.id])]) if i.analytic_tag_id else None,
					'name': i.name if i.name else self.glosa,
					'currency_id': i.currency_id.id,
					'amount_currency': i.importe_divisa if i.currency_id else 0,
					'debit': i.debe,
					'credit': i.haber,
					'date_maturity':i.fecha_vencimiento,
					'company_id': self.company_id.id,
					'reconciled':False,
					'tc': self.tc,
					'cash_flow_id': self.cash_flow_id.id,
				})
			lineas.append(vals)
		
		flag = True

		data = {
			'company_id': self.company_id.id,
			'partner_id': self.partner_cash_id.id if self.partner_cash_id else None,
			'l10n_latam_document_type_id': self.type_document_cash_id.id if self.type_document_cash_id else None,
			'journal_id': self.journal_id.id,
			'date': self.payment_date,
			'invoice_date': self.payment_date,
			'line_ids':lineas,
			'ref': self.nro_operation,
			'glosa':self.glosa,
			'td_payment_id': self.catalog_payment_id.id if self.catalog_payment_id else None,
			'move_type':'entry',
			'currency_rate':self.tc
		}

		if self.move_name and self.journal_move.id == self.journal_id.id and self.date_move == self.payment_date:
			data['name']= self.move_name
			flag = False
		else:
			self.journal_move = self.journal_id.id
			self.date_move = self.payment_date
			flag = True

		move_id = self.env['account.move'].create(data)
		if not flag:
			move_id.name = self.move_name
		
		move_id.post()

		if flag:
			self.move_name = move_id.name
		self.asiento_id._compute_amount()
		for c,elemnt in enumerate(self.invoice_ids):
			self.env['account.move.line'].browse([move_id.line_ids[c].id,self.invoice_ids[c].invoice_id.id]).reconcile()

		self.asiento_id = move_id.id
		self.state = 'done'

	def cancelar(self):
		if self.asiento_id.id:
			if self.asiento_id.state =='draft':
				pass
			else:
				for mm in self.asiento_id.line_ids:
					mm.remove_move_reconcile()
				self.asiento_id.button_cancel()
			self.asiento_id.line_ids.unlink()
			self.asiento_id.name = "/"
			self.asiento_id.unlink()

		self.state = 'draft'

	def unlink(self):
		for multi in self:
			if multi.state in ('done'):
				raise UserError("No puede eliminar un Pago Multiple que esta Finalizado")
		return super(MultipaymentAdvanceIt, self).unlink()

	def action_change_name_it(self):
		for multi in self:
			if multi.state == 'draft':
				multi.move_name = None
			else:
				raise UserError("No puede alterar la secuencia si no se encuentra en estado Borrador")

		return self.env['popup.it'].get_message('Se borro correctamente la secuencia.')
	
	def import_invoice_lines(self):
		wizard = self.env['import.multipayment.invoice.line.wizard'].create({
			'multipayment_id':self.id
			})
		module = __name__.split('addons.')[1].split('.')[0]
		view = self.env.ref('%s.view_import_multipayment_invoice_line_wizard_form' % module)
		return {
			'name':u'Importar Facturas',
			'res_id':wizard.id,
			'view_mode': 'form',
			'res_model': 'import.multipayment.invoice.line.wizard',
			'view_id': view.id,
			'target': 'new',
			'type': 'ir.actions.act_window',
		}
	
	def validate_lines(self):
		self.env.cr.execute("""SELECT nro_comp FROM account_move_line WHERE id in (
								SELECT invoice_id FROM multipayment_advance_it_line WHERE main_id = %d
								GROUP BY invoice_id
								HAVING count(invoice_id)>1)"""%(self.id))

		res = self.env.cr.dictfetchall()
		prob = False
		problemas = ""
		if len(res)>0:
			prob = True
			problemas += "LOS SIGUIENTES COMPROBANTES ESTAN DUPLICADOS EN LAS LINEAS DE PAGOS MULTIPLES: \n"
			for line in res:
				problemas += "• " + line['nro_comp'] + '\n'

		self.env.cr.execute("""select aml.nro_comp from multipayment_advance_it_line l
								left join account_move_line aml on aml.id = l.invoice_id
								where ((l.saldo<0 and (l.saldo)*-1 < l.importe_divisa ) or (l.saldo>0 and l.saldo < (l.importe_divisa)*-1))
								and l.main_id = %d"""%(self.id))

		res2 = self.env.cr.dictfetchall()
		if len(res2)>0:
			prob = True
			problemas += "LOS SIGUIENTES COMPROBANTES EXCEDEN EN MONTO DIVISA AL SALDO: \n"
			for line in res2:
				problemas += "• " + line['nro_comp'] + '\n'
		return prob, problemas

class MultipaymentAdvanceItLine(models.Model):
	_name = 'multipayment.advance.it.line'

	main_id = fields.Many2one('multipayment.advance.it')
	partner_id = fields.Many2one('res.partner',string='Partner')
	tipo_documento = fields.Many2one('l10n_latam.document.type',string='Tipo de Documento')	
	invoice_id = fields.Many2one('account.move.line',string='Factura')
	operation_type = fields.Char(string='T. Operacion', help=u'Sirve para los TXT Detracciones, si este campo se deja vacío se considerará "01"',size=2)
	good_services = fields.Char(string='Bien o Servicio', help=u'Sirve para los TXT Detracciones')
	account_id = fields.Many2one('account.account',string='Cuenta',related='invoice_id.account_id')
	currency_id = fields.Many2one('res.currency',string='Moneda',related='invoice_id.currency_id')
	fecha_vencimiento = fields.Date(string='Fecha Vencimiento',related='invoice_id.date_maturity')
	saldo = fields.Monetary(string='Saldo')
	importe_divisa = fields.Float(string='Importe Divisa',digits=(12,2))
	debe = fields.Float(string='Debe',digits=(12,2),default=0)
	haber = fields.Float(string='Haber',digits=(12,2),default=0)
	cta_abono = fields.Many2one('res.partner.bank',domain="[('partner_id','=',partner_id)]", string='Cta. Abono')

	@api.onchange('partner_id')
	def on_change_partner_id(self):
		self.cta_abono = False
		if self.partner_id:
			if self.main_id.is_detraction_payment==False:
				ctasp = self.partner_id.bank_ids.search([('partner_id','=',self.partner_id.id)],limit=1)
				if ctasp:
					self.cta_abono = ctasp.id

	@api.onchange('invoice_id')
	def on_change_invoice_id(self):
		if self.invoice_id:
			residual_amount = 0
			if self.invoice_id.currency_id:
				residual_amount = self.invoice_id.amount_residual_currency
			else:
				residual_amount = self.invoice_id.amount_residual
			self.saldo = residual_amount
			self.operation_type = self.invoice_id.move_id.type_op_det
			self.good_services = self.invoice_id.move_id.detraction_percent_id.code

	@api.onchange('importe_divisa')
	def _update_debit_credit(self):
		if self.importe_divisa:
			if self.invoice_id.currency_id and self.invoice_id.currency_id != self.invoice_id.company_id.currency_id:
				self.debe = self.importe_divisa * self.main_id.tc if self.importe_divisa > 0 else 0
				self.haber = 0 if self.importe_divisa > 0 else abs(self.importe_divisa * self.main_id.tc)
			else:
				self.debe = self.importe_divisa if self.importe_divisa > 0 else 0
				self.haber = 0 if self.importe_divisa > 0 else abs(self.importe_divisa)

class MultipaymentAdvanceItLine2(models.Model):
	_name = 'multipayment.advance.it.line2'

	main_id = fields.Many2one('multipayment.advance.it')
	name = fields.Char(string=u'Descripción')
	account_id = fields.Many2one('account.account',string='Cuenta')
	currency_id = fields.Many2one('res.currency',string='Moneda')	
	importe_divisa = fields.Float(string='Importe Divisa',digits=(12,2),default=0)
	partner_id = fields.Many2one('res.partner',string='Partner')
	type_document_id = fields.Many2one('l10n_latam.document.type',string='Tipo de Documento')
	nro_comp = fields.Char(string='Nro Comprobante')
	analytic_account_id = fields.Many2one('account.analytic.account', string='Cta Analitica')
	analytic_tag_id = fields.Many2one('account.analytic.tag', string='Etiqueta Analitica')
	debe = fields.Float(string='Debe',digits=(12,2))
	haber = fields.Float(string='Haber',digits=(12,2))
	fecha_vencimiento = fields.Date(string='Fecha Vencimiento')

	@api.onchange('importe_divisa','currency_id')
	def _update_debit_credit(self):
		if self.importe_divisa:
			if self.currency_id and self.currency_id != self.main_id.company_id.currency_id:
				self.debe = self.importe_divisa * self.main_id.tc if self.importe_divisa > 0 else 0
				self.haber = 0 if self.importe_divisa > 0 else abs(self.importe_divisa * self.main_id.tc)
			else:
				self.debe = self.importe_divisa if self.importe_divisa > 0 else 0
				self.haber = 0 if self.importe_divisa > 0 else abs(self.importe_divisa)
	
	