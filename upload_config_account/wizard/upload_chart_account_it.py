# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError

class UploadChartAccountIt(models.TransientModel):
	_name = "upload.chart.account.it"

	upload_account_parameter = fields.Boolean(string='Actualizar Parametros Principales',default=False)
	direct_file = fields.Char(string='Directorio para reportes')
	upload_account_journal = fields.Boolean(string='Cargar Diarios',default=False)
	upload_account_tax = fields.Boolean(string='Crear Impuestos',default=False)

	def upload_chart(self):
		if self.upload_account_tax:
			self.upload_chart_tax()

		if self.upload_account_journal:
			self.upload_chart_journal()

		if self.upload_account_parameter:
			self.upload_chart_parameter()
		
		return self.env['popup.it'].get_message('SE CARGO LAS CONFIGURACIONES DE MANERA CORRECTA.')

	def upload_chart_parameter(self):
		obj_parameter = self.env['account.main.parameter']
		main_parameter = obj_parameter.search([('company_id','=',self.env.company.id)],limit=1)

		if not main_parameter:
			main_parameter = obj_parameter.create({
				'company_id':self.env.company.id
				})
		
		obj_partner = self.env['res.partner']
		doc_anul = obj_partner.search([('name','=','DOCUMENTOS ANULADOS'),('vat','=','00000000000')])
		if not doc_anul:
			obj_partner.create({
				'name': 'DOCUMENTOS ANULADOS',
				'vat': '00000000000',
				'company_type':'person'
			})
		
		boleta = obj_partner.search([('name','=','BOLETAS DE VENTAS'),('vat','=','00000000002')])
		if not boleta:
			obj_partner.create({
				'name': 'BOLETAS DE VENTAS',
				'vat': '00000000002',
				'company_type':'person'
			})

		self.env.cr.execute("""select update_main_parameter(%d,'%s',%d)"""%(self.env.company.id,self.direct_file,main_parameter.id))

		main_parameter.free_transer_tax_ids = [(6, 0, self.env['account.tax'].search([('name','in',['IGV-TRG','TRF-GRAT']),('company_id','=',self.env.company.id)]).ids)]
		

	def upload_chart_journal(self):
		obj = self.env['account.journal']
		
		aut = obj.search([('code','=','AUT'),('company_id','=',self.env.company.id)],limit=1)
		if not aut:
			aut = obj.create({
				'name': u'Asientos Automáticos',
				'code': 'AUT',
				'type': 'general',
				'company_id': self.env.company.id
			})

		pdet = obj.search([('code','=','PDET'),('company_id','=',self.env.company.id)],limit=1)
		if not pdet:
			pdet = obj.create({
				'name': u'Provisión de Detracciones',
				'code': 'PDET',
				'type': 'general',
				'company_id': self.env.company.id
			})

		anc = obj.search([('code','=','ANC'),('company_id','=',self.env.company.id)],limit=1)
		if not anc:
			anc = obj.create({
				'name': u'Aplicación de Notas de Crédito',
				'code': 'ANC',
				'type': 'general',
				'company_id': self.env.company.id
			})
		transf = obj.search([('code','=','TRG'),('company_id','=',self.env.company.id)],limit=1)
		if not transf:
			anc = obj.create({
				'name':'Reversiones Tranferencias Gratuitas',
				'code': 'TRG',
				'type': 'general',
				'company_id': self.env.company.id
			})

	def upload_chart_tax(self):
		obj = self.env['account.tax']

		#self.env.cr.execute("""SELECT COUNT(id) as data FROM account_move_line where company_id = %s""" % (str(self.env.company.id)))
		#data = self.env.cr.fetchall()
		#if data[0][0] > 0:
		#	raise UserError(u'Si ya existe data en esta Compañía no puede usar la opcion "Crear Impuestos"')

		#taxes_delete = obj.search([('company_id','=',self.env.company.id)])

		#posc = self.env['account.fiscal.position'].search([('company_id','=',self.env.company.id)])
		#posc.tax_ids.unlink()

		#for i in taxes_delete:
		#	i.unlink()
		
		if not self.env.company.country_id:
			raise UserError(u'Falta configurar País en su Compañía para crear sus impuestos.')
		self._check_tags()

		obj.create({
			'name': 'IGV1',
			'type_tax_use': 'purchase',
			'amount_type': 'percent',
			'active': True,
			'company_id': self.env.company.id,
			'country_id': self.env.company.country_id.id,
			'sequence': 1,
			'amount': 18,
			'description': 'IGV1',
			'price_include':False,
			'include_base_amount':False,
			'tax_group_id': 1,
			'tax_exigibility':'on_invoice',
			'invoice_repartition_line_ids': [
				(0, 0, { 'repartition_type': 'base', 
						'factor_percent': 100.0,
						'company_id': self.env.company.id, 
						'tag_ids': [(6, 0, [self.env['account.account.tag'].search([('name','=','BASE1')], limit=1).id])]}),
				(0, 0, { 'repartition_type': 'tax', 
						'factor_percent': 100.0,
						'company_id': self.env.company.id, 
						'account_id': self.env['account.account'].search([('code','=','4011100'),('company_id','=',self.env.company.id)], limit=1).id,
						'tag_ids': [(6, 0, [self.env['account.account.tag'].search([('name','=','IGV1')], limit=1).id])]}),
			],
			'refund_repartition_line_ids': [
				(0, 0, { 'repartition_type': 'base', 
						'factor_percent': 100.0,
						'company_id': self.env.company.id,
						'tag_ids': [(6, 0, [self.env['account.account.tag'].search([('name','=','BASE1')], limit=1).id])]}),
				(0, 0, { 'repartition_type': 'tax', 
						'factor_percent': 100.0,
						'company_id': self.env.company.id,
						'account_id': self.env['account.account'].search([('code','=','4011100'),('company_id','=',self.env.company.id)], limit=1).id,
						'tag_ids': [(6, 0, [self.env['account.account.tag'].search([('name','=','IGV1')], limit=1).id])]}),
			]
		})

		obj.create({
			'name': 'IGV2',
			'type_tax_use': 'purchase',
			'amount_type': 'percent',
			'active': True,
			'company_id': self.env.company.id,
			'country_id': self.env.company.country_id.id,
			'sequence': 2,
			'amount': 18,
			'description': 'IGV2',
			'price_include':False,
			'include_base_amount':False,
			'tax_group_id': 1,
			'tax_exigibility':'on_invoice',
			'invoice_repartition_line_ids': [
				(0, 0, { 'repartition_type': 'base', 
						'factor_percent': 100.0,
						'company_id': self.env.company.id, 
						'tag_ids': [(6, 0, [self.env['account.account.tag'].search([('name','=','BASE2')], limit=1).id])]}),
				(0, 0, { 'repartition_type': 'tax', 
						'factor_percent': 100.0,
						'company_id': self.env.company.id,
						'account_id': self.env['account.account'].search([('code','=','4011100'),('company_id','=',self.env.company.id)], limit=1).id,
						'tag_ids': [(6, 0, [self.env['account.account.tag'].search([('name','=','IGV2')], limit=1).id])]}),
			],
			'refund_repartition_line_ids': [
				(0, 0, { 'repartition_type': 'base', 
						'factor_percent': 100.0,
						'company_id': self.env.company.id,
						'tag_ids': [(6, 0, [self.env['account.account.tag'].search([('name','=','BASE2')], limit=1).id])]}),
				(0, 0, { 'repartition_type': 'tax', 
						'factor_percent': 100.0,
						'company_id': self.env.company.id,
						'account_id': self.env['account.account'].search([('code','=','4011100'),('company_id','=',self.env.company.id)], limit=1).id,
						'tag_ids': [(6, 0, [self.env['account.account.tag'].search([('name','=','IGV2')], limit=1).id])]}),
			]
		})

		obj.create({
			'name': 'IGV3',
			'type_tax_use': 'purchase',
			'amount_type': 'percent',
			'active': True,
			'company_id': self.env.company.id,
			'country_id': self.env.company.country_id.id,
			'sequence': 3,
			'amount': 18,
			'description': 'IGV3',
			'price_include':False,
			'include_base_amount':False,
			'tax_group_id': 1,
			'tax_exigibility':'on_invoice',
			'invoice_repartition_line_ids': [
				(0, 0, { 'repartition_type': 'base', 
						'factor_percent': 100.0,
						'company_id': self.env.company.id,
						'tag_ids': [(6, 0, [self.env['account.account.tag'].search([('name','=','BASE3')], limit=1).id])]}),
				(0, 0, { 'repartition_type': 'tax', 
						'factor_percent': 100.0,
						'company_id': self.env.company.id,
						'account_id': self.env['account.account'].search([('code','=','4011100'),('company_id','=',self.env.company.id)], limit=1).id,
						'tag_ids': [(6, 0, [self.env['account.account.tag'].search([('name','=','IGV3')], limit=1).id])]}),
			],
			'refund_repartition_line_ids': [
				(0, 0, { 'repartition_type': 'base', 
						'factor_percent': 100.0,
						'company_id': self.env.company.id,
						'tag_ids': [(6, 0, [self.env['account.account.tag'].search([('name','=','BASE3')], limit=1).id])]}),
				(0, 0, { 'repartition_type': 'tax', 
						'factor_percent': 100.0,
						'company_id': self.env.company.id,
						'account_id': self.env['account.account'].search([('code','=','4011100'),('company_id','=',self.env.company.id)], limit=1).id,
						'tag_ids': [(6, 0, [self.env['account.account.tag'].search([('name','=','IGV3')], limit=1).id])]}),
			]
		})

		obj.create({
			'name': 'CNG',
			'type_tax_use': 'purchase',
			'amount_type': 'percent',
			'active': True,
			'company_id': self.env.company.id,
			'country_id': self.env.company.country_id.id,
			'sequence': 4,
			'amount': 0,
			'description': 'CNG',
			'price_include':False,
			'include_base_amount':False,
			'tax_group_id': 1,
			'tax_exigibility':'on_invoice',
			'invoice_repartition_line_ids': [
				(0, 0, { 'repartition_type': 'base', 
						'factor_percent': 100.0,
						'company_id': self.env.company.id,
						'tag_ids': [(6, 0, [self.env['account.account.tag'].search([('name','=','CNG')], limit=1).id])]}),
				(0, 0, { 'repartition_type': 'tax', 
						'factor_percent': 100.0,
						'company_id': self.env.company.id,
						'tag_ids': []}),
			],
			'refund_repartition_line_ids': [
				(0, 0, { 'repartition_type': 'base', 
						'factor_percent': 100.0,
						'company_id': self.env.company.id,
						'tag_ids': [(6, 0, [self.env['account.account.tag'].search([('name','=','CNG')], limit=1).id])]}),
				(0, 0, { 'repartition_type': 'tax', 
						'factor_percent': 100.0,
						'company_id': self.env.company.id,
						'tag_ids': []}),
			]
		})

		obj.create({
			'name': 'OTROS-C',
			'type_tax_use': 'purchase',
			'amount_type': 'percent',
			'active': True,
			'company_id': self.env.company.id,
			'country_id': self.env.company.country_id.id,
			'sequence': 5,
			'amount': 0,
			'description': 'OTROS-C',
			'price_include':False,
			'include_base_amount':False,
			'tax_group_id': 1,
			'tax_exigibility':'on_invoice',
			'invoice_repartition_line_ids': [
				(0, 0, { 'repartition_type': 'base', 
						'factor_percent': 100.0,
						'company_id': self.env.company.id,
						'tag_ids': [(6, 0, [self.env['account.account.tag'].search([('name','=','OTROS-C')], limit=1).id])]}),
				(0, 0, { 'repartition_type': 'tax', 
						'factor_percent': 100.0,
						'company_id': self.env.company.id,
						'tag_ids': []}),
			],
			'refund_repartition_line_ids': [
				(0, 0, { 'repartition_type': 'base', 
						'factor_percent': 100.0,
						'company_id': self.env.company.id,
						'tag_ids': [(6, 0, [self.env['account.account.tag'].search([('name','=','OTROS-C')], limit=1).id])]}),
				(0, 0, { 'repartition_type': 'tax', 
						'factor_percent': 100.0,
						'company_id': self.env.company.id,
						'tag_ids': []}),
			]
		})

		obj.create({
			'name': u'4TA0%',
			'type_tax_use': 'purchase',
			'amount_type': 'percent',
			'active': True,
			'company_id': self.env.company.id,
			'country_id': self.env.company.country_id.id,
			'sequence': 6,
			'amount': 0,
			'description': u'4TA0%',
			'price_include':False,
			'include_base_amount':False,
			'tax_group_id': 1,
			'tax_exigibility':'on_invoice',
			'invoice_repartition_line_ids': [
				(0, 0, { 'repartition_type': 'base', 
						'factor_percent': 100.0,
						'company_id': self.env.company.id,
						'tag_ids': [(6, 0, [self.env['account.account.tag'].search([('name','=','RENTA 4TA')], limit=1).id])]}),
				(0, 0, { 'repartition_type': 'tax', 
						'factor_percent': 100.0,
						'company_id': self.env.company.id,
						'tag_ids': []}),
			],
			'refund_repartition_line_ids': [
				(0, 0, { 'repartition_type': 'base', 
						'factor_percent': 100.0,
						'company_id': self.env.company.id,
						'tag_ids': [(6, 0, [self.env['account.account.tag'].search([('name','=','RENTA 4TA')], limit=1).id])]}),
				(0, 0, { 'repartition_type': 'tax', 
						'factor_percent': 100.0,
						'company_id': self.env.company.id,
						'tag_ids': []}),
			]
		})

		obj.create({
			'name': u'4TA8%',
			'type_tax_use': 'purchase',
			'amount_type': 'percent',
			'active': True,
			'company_id': self.env.company.id,
			'country_id': self.env.company.country_id.id,
			'sequence': 7,
			'amount': -8,
			'description': u'4TA8%',
			'price_include':False,
			'include_base_amount':False,
			'tax_group_id': 1,
			'tax_exigibility':'on_invoice',
			'invoice_repartition_line_ids': [
				(0, 0, { 'repartition_type': 'base', 
						'factor_percent': 100.0,
						'company_id': self.env.company.id,
						'tag_ids': [(6, 0, [self.env['account.account.tag'].search([('name','=','RENTA 4TA')], limit=1).id])]}),
				(0, 0, { 'repartition_type': 'tax', 
						'factor_percent': 100.0,
						'company_id': self.env.company.id,
						'account_id': self.env['account.account'].search([('code','=','4017200'),('company_id','=',self.env.company.id)], limit=1).id,
						'tag_ids': [(6, 0, [self.env['account.account.tag'].search([('name','=','RET 4TA')], limit=1).id])]}),
			],
			'refund_repartition_line_ids': [
				(0, 0, { 'repartition_type': 'base', 
						'factor_percent': 100.0,
						'company_id': self.env.company.id,
						'tag_ids': [(6, 0, [self.env['account.account.tag'].search([('name','=','RENTA 4TA')], limit=1).id])]}),
				(0, 0, { 'repartition_type': 'tax', 
						'factor_percent': 100.0,
						'company_id': self.env.company.id,
						'account_id': self.env['account.account'].search([('code','=','4017200'),('company_id','=',self.env.company.id)], limit=1).id,
						'tag_ids': [(6, 0, [self.env['account.account.tag'].search([('name','=','RET 4TA')], limit=1).id])]}),
			]
		})

		obj.create({
			'name': 'EXO',
			'type_tax_use': 'sale',
			'amount_type': 'percent',
			'active': True,
			'company_id': self.env.company.id,
			'country_id': self.env.company.country_id.id,
			'sequence': 8,
			'amount': 0,
			'description': 'EXO',
			'price_include':False,
			'include_base_amount':False,
			'tax_group_id': 1,
			'tax_exigibility':'on_invoice',
			'invoice_repartition_line_ids': [
				(0, 0, { 'repartition_type': 'base', 
						'factor_percent': 100.0,
						'company_id': self.env.company.id,
						'tag_ids': [(6, 0, [self.env['account.account.tag'].search([('name','=','EXO')], limit=1).id])]}),
				(0, 0, { 'repartition_type': 'tax', 
						'factor_percent': 100.0,
						'company_id': self.env.company.id,
						'tag_ids': []}),
			],
			'refund_repartition_line_ids': [
				(0, 0, { 'repartition_type': 'base', 
						'factor_percent': 100.0,
						'company_id': self.env.company.id,
						'tag_ids': [(6, 0, [self.env['account.account.tag'].search([('name','=','EXO')], limit=1).id])]}),
				(0, 0, { 'repartition_type': 'tax', 
						'factor_percent': 100.0,
						'company_id': self.env.company.id,
						'tag_ids': []}),
			]
		})

		obj.create({
			'name': 'EXP',
			'type_tax_use': 'sale',
			'amount_type': 'percent',
			'active': True,
			'company_id': self.env.company.id,
			'country_id': self.env.company.country_id.id,
			'sequence': 9,
			'amount': 0,
			'description': 'EXP',
			'price_include':False,
			'include_base_amount':False,
			'tax_group_id': 1,
			'tax_exigibility':'on_invoice',
			'invoice_repartition_line_ids': [
				(0, 0, { 'repartition_type': 'base', 
						'factor_percent': 100.0,
						'company_id': self.env.company.id,
						'tag_ids': [(6, 0, [self.env['account.account.tag'].search([('name','=','EXP')], limit=1).id])]}),
				(0, 0, { 'repartition_type': 'tax', 
						'factor_percent': 100.0,
						'company_id': self.env.company.id,
						'tag_ids': []}),
			],
			'refund_repartition_line_ids': [
				(0, 0, { 'repartition_type': 'base', 
						'factor_percent': 100.0,
						'company_id': self.env.company.id,
						'tag_ids': [(6, 0, [self.env['account.account.tag'].search([('name','=','EXP')], limit=1).id])]}),
				(0, 0, { 'repartition_type': 'tax', 
						'factor_percent': 100.0,
						'company_id': self.env.company.id,
						'tag_ids': []}),
			]
		})

		obj.create({
			'name': 'INAF',
			'type_tax_use': 'sale',
			'amount_type': 'percent',
			'active': True,
			'company_id': self.env.company.id,
			'country_id': self.env.company.country_id.id,
			'sequence': 10,
			'amount': 0,
			'description': 'INAF',
			'price_include':False,
			'include_base_amount':False,
			'tax_group_id': 1,
			'tax_exigibility':'on_invoice',
			'invoice_repartition_line_ids': [
				(0, 0, { 'repartition_type': 'base', 
						'factor_percent': 100.0,
						'company_id': self.env.company.id,
						'tag_ids': [(6, 0, [self.env['account.account.tag'].search([('name','=','INAF')], limit=1).id])]}),
				(0, 0, { 'repartition_type': 'tax', 
						'factor_percent': 100.0,
						'company_id': self.env.company.id,
						'tag_ids': []}),
			],
			'refund_repartition_line_ids': [
				(0, 0, { 'repartition_type': 'base', 
						'factor_percent': 100.0,
						'company_id': self.env.company.id,
						'tag_ids': [(6, 0, [self.env['account.account.tag'].search([('name','=','INAF')], limit=1).id])]}),
				(0, 0, { 'repartition_type': 'tax', 
						'factor_percent': 100.0,
						'company_id': self.env.company.id,
						'tag_ids': []}),
			]
		})

		obj.create({
			'name': 'IGV-VEN',
			'type_tax_use': 'sale',
			'amount_type': 'percent',
			'active': True,
			'company_id': self.env.company.id,
			'country_id': self.env.company.country_id.id,
			'sequence': 11,
			'amount': 18,
			'description': 'IGV-V',
			'price_include':False,
			'include_base_amount':False,
			'tax_group_id': 1,
			'tax_exigibility':'on_invoice',
			'invoice_repartition_line_ids': [
				(0, 0, { 'repartition_type': 'base', 
						'factor_percent': 100.0,
						'company_id': self.env.company.id,
						'tag_ids': [(6, 0, [self.env['account.account.tag'].search([('name','=','VENTA-G')], limit=1).id])]}),
				(0, 0, { 'repartition_type': 'tax', 
						'factor_percent': 100.0,
						'company_id': self.env.company.id,
						'account_id': self.env['account.account'].search([('code','=','4011100'),('company_id','=',self.env.company.id)], limit=1).id,
						'tag_ids': [(6, 0, [self.env['account.account.tag'].search([('name','=','IGV-V')], limit=1).id])]}),
			],
			'refund_repartition_line_ids': [
				(0, 0, { 'repartition_type': 'base', 
						'factor_percent': 100.0,
						'company_id': self.env.company.id,
						'tag_ids': [(6, 0, [self.env['account.account.tag'].search([('name','=','VENTA-G')], limit=1).id])]}),
				(0, 0, { 'repartition_type': 'tax', 
						'factor_percent': 100.0,
						'company_id': self.env.company.id,
						'account_id': self.env['account.account'].search([('code','=','4011100'),('company_id','=',self.env.company.id)], limit=1).id,
						'tag_ids': [(6, 0, [self.env['account.account.tag'].search([('name','=','IGV-V')], limit=1).id])]}),
			]
		})

		obj.create({
			'name': 'ICBPER-V',
			'type_tax_use': 'sale',
			'amount_type': 'fixed',
			'active': True,
			'company_id': self.env.company.id,
			'country_id': self.env.company.country_id.id,
			'sequence': 16,
			'amount': 0.3,
			'description': 'ICBPER-V',
			'price_include':False,
			'include_base_amount':False,
			'tax_group_id': 1,
			'tax_exigibility':'on_invoice',
			'invoice_repartition_line_ids': [
				(0, 0, { 'repartition_type': 'base',
						'factor_percent': 100.0,
						'company_id': self.env.company.id,
						'tag_ids': []}),
				(0, 0, { 'repartition_type': 'tax', 
						'factor_percent': 100.0,
						'company_id': self.env.company.id,
						'account_id': self.env['account.account'].search([('code','=','4018900'),('company_id','=',self.env.company.id)], limit=1).id,
						'tag_ids': [(6, 0, [self.env['account.account.tag'].search([('name','=','ICBPER-V')], limit=1).id])]}),
			],
			'refund_repartition_line_ids': [
				(0, 0, { 'repartition_type': 'base',
						'factor_percent': 100.0,
						'company_id': self.env.company.id,
						'tag_ids': []}),
				(0, 0, { 'repartition_type': 'tax', 
						'factor_percent': 100.0,
						'company_id': self.env.company.id,
						'account_id': self.env['account.account'].search([('code','=','4018900'),('company_id','=',self.env.company.id)], limit=1).id,
						'tag_ids': [(6, 0, [self.env['account.account.tag'].search([('name','=','ICBPER-V')], limit=1).id])]}),
			]
		})

		obj.create({
			'name': 'ICBPER-C',
			'type_tax_use': 'purchase',
			'amount_type': 'fixed',
			'active': True,
			'company_id': self.env.company.id,
			'country_id': self.env.company.country_id.id,
			'sequence': 17,
			'amount': 0.3,
			'description': 'ICBPER-C',
			'price_include':False,
			'include_base_amount':False,
			'tax_group_id': 1,
			'tax_exigibility':'on_invoice',
			'invoice_repartition_line_ids': [
				(0, 0, { 'repartition_type': 'base',
						'factor_percent': 100.0,
						'company_id': self.env.company.id,
						'tag_ids': []}),
				(0, 0, { 'repartition_type': 'tax', 
						'factor_percent': 100.0,
						'company_id': self.env.company.id,
						'account_id': self.env['account.account'].search([('code','=','6419000'),('company_id','=',self.env.company.id)], limit=1).id,
						'tag_ids': [(6, 0, [self.env['account.account.tag'].search([('name','=','ICBPER-C')], limit=1).id])]}),
			],
			'refund_repartition_line_ids': [
				(0, 0, { 'repartition_type': 'base',
						'factor_percent': 100.0,
						'company_id': self.env.company.id,
						'tag_ids': []}),
				(0, 0, { 'repartition_type': 'tax', 
						'factor_percent': 100.0,
						'company_id': self.env.company.id,
						'account_id': self.env['account.account'].search([('code','=','6419000'),('company_id','=',self.env.company.id)], limit=1).id,
						'tag_ids': [(6, 0, [self.env['account.account.tag'].search([('name','=','ICBPER-C')], limit=1).id])]}),
			]
		})

		obj.create({
			'name': 'OTROS-V',
			'type_tax_use': 'sale',
			'amount_type': 'percent',
			'active': True,
			'company_id': self.env.company.id,
			'country_id': self.env.company.country_id.id,
			'sequence': 12,
			'amount': 0,
			'description': 'OTROS-V',
			'price_include':False,
			'include_base_amount':False,
			'tax_group_id': 1,
			'tax_exigibility':'on_invoice',
			'invoice_repartition_line_ids': [
				(0, 0, { 'repartition_type': 'base', 
						'factor_percent': 100.0,
						'company_id': self.env.company.id,
						'tag_ids': [(6, 0, [self.env['account.account.tag'].search([('name','=','OTROS-V')], limit=1).id])]}),
				(0, 0, { 'repartition_type': 'tax', 
						'factor_percent': 100.0,
						'company_id': self.env.company.id,
						'tag_ids': []}),
			],
			'refund_repartition_line_ids': [
				(0, 0, { 'repartition_type': 'base', 
						'factor_percent': 100.0,
						'company_id': self.env.company.id,
						'tag_ids': [(6, 0, [self.env['account.account.tag'].search([('name','=','OTROS-V')], limit=1).id])]}),
				(0, 0, { 'repartition_type': 'tax', 
						'factor_percent': 100.0,
						'company_id': self.env.company.id,
						'tag_ids': []}),
			]
		})

		obj.create({
			'name': 'IGV-INC-C',
			'type_tax_use': 'purchase',
			'amount_type': 'percent',
			'active': True,
			'company_id': self.env.company.id,
			'country_id': self.env.company.country_id.id,
			'sequence': 13,
			'amount': 18,
			'description': 'IGV-INC-C',
			'price_include':True,
			'include_base_amount':False,
			'tax_group_id': 1,
			'tax_exigibility':'on_invoice',
			'invoice_repartition_line_ids': [
				(0, 0, { 'repartition_type': 'base', 
						'factor_percent': 100.0,
						'company_id': self.env.company.id,
						'tag_ids': [(6, 0, [self.env['account.account.tag'].search([('name','=','BASE1')], limit=1).id])]}),
				(0, 0, { 'repartition_type': 'tax', 
						'factor_percent': 100.0,
						'company_id': self.env.company.id,
						'account_id': self.env['account.account'].search([('code','=','4011100'),('company_id','=',self.env.company.id)], limit=1).id,
						'tag_ids': [(6, 0, [self.env['account.account.tag'].search([('name','=','IGV1')], limit=1).id])]}),
			],
			'refund_repartition_line_ids': [
				(0, 0, { 'repartition_type': 'base', 
						'factor_percent': 100.0,
						'company_id': self.env.company.id,
						'tag_ids': [(6, 0, [self.env['account.account.tag'].search([('name','=','BASE1')], limit=1).id])]}),
				(0, 0, { 'repartition_type': 'tax', 
						'factor_percent': 100.0,
						'company_id': self.env.company.id,
						'account_id': self.env['account.account'].search([('code','=','4011100'),('company_id','=',self.env.company.id)], limit=1).id,
						'tag_ids': [(6, 0, [self.env['account.account.tag'].search([('name','=','IGV1')], limit=1).id])]}),
			]
		})

		obj.create({
			'name': 'IGV-INC-V',
			'type_tax_use': 'sale',
			'amount_type': 'percent',
			'active': True,
			'company_id': self.env.company.id,
			'country_id': self.env.company.country_id.id,
			'sequence': 14,
			'amount': 18,
			'description': 'IGV-INC-V',
			'price_include':True,
			'include_base_amount':False,
			'tax_group_id': 1,
			'tax_exigibility':'on_invoice',
			'invoice_repartition_line_ids': [
				(0, 0, { 'repartition_type': 'base', 
						'factor_percent': 100.0,
						'company_id': self.env.company.id,
						'tag_ids': [(6, 0, [self.env['account.account.tag'].search([('name','=','VENTA-G')], limit=1).id])]}),
				(0, 0, { 'repartition_type': 'tax', 
						'factor_percent': 100.0,
						'company_id': self.env.company.id,
						'account_id': self.env['account.account'].search([('code','=','4011100'),('company_id','=',self.env.company.id)], limit=1).id,
						'tag_ids': [(6, 0, [self.env['account.account.tag'].search([('name','=','IGV-V')], limit=1).id])]}),
			],
			'refund_repartition_line_ids': [
				(0, 0, { 'repartition_type': 'base', 
						'factor_percent': 100.0,
						'company_id': self.env.company.id,
						'tag_ids': [(6, 0, [self.env['account.account.tag'].search([('name','=','VENTA-G')], limit=1).id])]}),
				(0, 0, { 'repartition_type': 'tax', 
						'factor_percent': 100.0,
						'company_id': self.env.company.id,
						'account_id': self.env['account.account'].search([('code','=','4011100'),('company_id','=',self.env.company.id)], limit=1).id,
						'tag_ids': [(6, 0, [self.env['account.account.tag'].search([('name','=','IGV-V')], limit=1).id])]}),
			]
		})

		obj.create({
			'name': 'PER-C',
			'type_tax_use': 'purchase',
			'amount_type': 'percent',
			'active': True,
			'company_id': self.env.company.id,
			'country_id': self.env.company.country_id.id,
			'sequence': 15,
			'amount': 0,
			'description': 'PER-C',
			'price_include':False,
			'include_base_amount':False,
			'tax_group_id': 1,
			'tax_exigibility':'on_invoice',
			'invoice_repartition_line_ids': [
				(0, 0, { 'repartition_type': 'base', 
						'factor_percent': 100.0,
						'company_id': self.env.company.id,
						'tag_ids': [(6, 0, [self.env['account.account.tag'].search([('name','=','PER-C')], limit=1).id])]}),
				(0, 0, { 'repartition_type': 'tax', 
						'factor_percent': 100.0,
						'company_id': self.env.company.id,
						'tag_ids': []}),
			],
			'refund_repartition_line_ids': [
				(0, 0, { 'repartition_type': 'base', 
						'factor_percent': 100.0,
						'company_id': self.env.company.id,
						'tag_ids': [(6, 0, [self.env['account.account.tag'].search([('name','=','PER-C')], limit=1).id])]}),
				(0, 0, { 'repartition_type': 'tax', 
						'factor_percent': 100.0,
						'company_id': self.env.company.id,
						'tag_ids': []}),
			]
		})

		obj.create({
			'name': 'IGV-TRG',
			'type_tax_use': 'sale',
			'amount_type': 'percent',
			'active': True,
			'company_id': self.env.company.id,
			'country_id': self.env.company.country_id.id,
			'sequence': 16,
			'amount': 18,
			'description': 'IGV-TRG',
			'price_include':False,
			'include_base_amount':False,
			'tax_group_id': 1,
			'tax_exigibility':'on_invoice',
			'invoice_repartition_line_ids': [
				(0, 0, { 'repartition_type': 'base', 
						'factor_percent': 100.0,
						'company_id': self.env.company.id,
						'tag_ids': [(6, 0, [self.env['account.account.tag'].search([('name','=','VENTA-G')], limit=1).id])]}),
				(0, 0, { 'repartition_type': 'tax', 
						'factor_percent': 100.0,
						'company_id': self.env.company.id,
						'account_id': self.env['account.account'].search([('code','=','4011100'),('company_id','=',self.env.company.id)], limit=1).id,
						'tag_ids': [(6, 0, [self.env['account.account.tag'].search([('name','=','IGV-V')], limit=1).id])]}),
			],
			'refund_repartition_line_ids': [
				(0, 0, { 'repartition_type': 'base', 
						'factor_percent': 100.0,
						'company_id': self.env.company.id,
						'tag_ids': [(6, 0, [self.env['account.account.tag'].search([('name','=','VENTA-G')], limit=1).id])]}),
				(0, 0, { 'repartition_type': 'tax', 
						'factor_percent': 100.0,
						'company_id': self.env.company.id,
						'account_id': self.env['account.account'].search([('code','=','4011100'),('company_id','=',self.env.company.id)], limit=1).id,
						'tag_ids': [(6, 0, [self.env['account.account.tag'].search([('name','=','IGV-V')], limit=1).id])]}),
			]
		})

		obj.create({
			'name': 'TRF-GRAT',
			'type_tax_use': 'sale',
			'amount_type': 'percent',
			'active': True,
			'company_id': self.env.company.id,
			'country_id': self.env.company.country_id.id,
			'sequence': 17,
			'amount': 0,
			'description': 'TRF-GRAT',
			'price_include':False,
			'include_base_amount':False,
			'tax_group_id': 1,
			'tax_exigibility':'on_invoice',
			'invoice_repartition_line_ids': [
				(0, 0, { 'repartition_type': 'base', 
						'factor_percent': 100.0,
						'company_id': self.env.company.id,
						'tag_ids': [(6, 0, [self.env['account.account.tag'].search([('name','=','INAF')], limit=1).id])]}),
				(0, 0, { 'repartition_type': 'tax', 
						'factor_percent': 100.0,
						'company_id': self.env.company.id,
						'tag_ids': []}),
			],
			'refund_repartition_line_ids': [
				(0, 0, { 'repartition_type': 'base', 
						'factor_percent': 100.0,
						'company_id': self.env.company.id,
						'tag_ids': [(6, 0, [self.env['account.account.tag'].search([('name','=','INAF')], limit=1).id])]}),
				(0, 0, { 'repartition_type': 'tax', 
						'factor_percent': 100.0,
						'company_id': self.env.company.id,
						'tag_ids': []}),
			]
		})

		
		self.env.company.account_sale_tax_id = self.env['account.tax'].search([('name','=','IGV-VEN'),('company_id','=',self.env.company.id)], limit=1).id
		self.env.company.account_purchase_tax_id = self.env['account.tax'].search([('name','=','IGV1'),('company_id','=',self.env.company.id)], limit=1).id

	def _check_tags(self):
		obj_tag = self.env['account.account.tag']

		base1_tag = obj_tag.search([('name','=','BASE1')], limit=1)

		if not base1_tag:
			obj_tag.create({
				'name': 'BASE1',
				'applicability':'taxes',
				'active': True,
				'country_id':self.env.company.country_id.id,
				'record_shop':'1',
				'sequence': 1
			})

		base2_tag = obj_tag.search([('name','=','BASE2')], limit=1)

		if not base2_tag:
			obj_tag.create({
				'name': 'BASE2',
				'applicability':'taxes',
				'active': True,
				'country_id':self.env.company.country_id.id,
				'record_shop':'2',
				'sequence': 2
			})

		base3_tag = obj_tag.search([('name','=','BASE3')], limit=1)

		if not base3_tag:
			obj_tag.create({
				'name': 'BASE3',
				'applicability':'taxes',
				'active': True,
				'country_id':self.env.company.country_id.id,
				'record_shop':'3',
				'sequence': 3
			})

		cng_tag = obj_tag.search([('name','=','CNG')], limit=1)

		if not cng_tag:
			obj_tag.create({
				'name': 'CNG',
				'applicability':'taxes',
				'active': True,
				'country_id':self.env.company.country_id.id,
				'record_shop':'4',
				'sequence': 4
			})

		iscc_tag = obj_tag.search([('name','=','ISC-C')], limit=1)

		if not iscc_tag:
			obj_tag.create({
				'name': 'ISC-C',
				'applicability':'taxes',
				'active': True,
				'country_id':self.env.company.country_id.id,
				'record_shop':'5',
				'sequence': 5
			})

		otrosc_tag = obj_tag.search([('name','=','OTROS-C')], limit=1)

		if not otrosc_tag:
			obj_tag.create({
				'name': 'OTROS-C',
				'applicability':'taxes',
				'active': True,
				'country_id':self.env.company.country_id.id,
				'record_shop':'6',
				'sequence': 6
			})

		igv1_tag = obj_tag.search([('name','=','IGV1')], limit=1)

		if not igv1_tag:
			obj_tag.create({
				'name': 'IGV1',
				'applicability':'taxes',
				'active': True,
				'country_id':self.env.company.country_id.id,
				'record_shop':'7',
				'sequence': 7
			})

		igv2_tag = obj_tag.search([('name','=','IGV2')], limit=1)

		if not igv2_tag:
			obj_tag.create({
				'name': 'IGV2',
				'applicability':'taxes',
				'active': True,
				'country_id':self.env.company.country_id.id,
				'record_shop':'8',
				'sequence': 8
			})

		igv3_tag = obj_tag.search([('name','=','IGV3')], limit=1)

		if not igv3_tag:
			obj_tag.create({
				'name': 'IGV3',
				'applicability':'taxes',
				'active': True,
				'country_id':self.env.company.country_id.id,
				'record_shop':'9',
				'sequence': 9
			})

		exp_tag = obj_tag.search([('name','=','EXP')], limit=1)

		if not exp_tag:
			obj_tag.create({
				'name': 'EXP',
				'applicability':'taxes',
				'active': True,
				'country_id':self.env.company.country_id.id,
				'record_sale':'1',
				'sequence': 10
			})

		ventag_tag = obj_tag.search([('name','=','VENTA-G')], limit=1)

		if not ventag_tag:
			obj_tag.create({
				'name': 'VENTA-G',
				'applicability':'taxes',
				'active': True,
				'country_id':self.env.company.country_id.id,
				'record_sale':'2',
				'sequence': 11
			})

		inaf_tag = obj_tag.search([('name','=','INAF')], limit=1)

		if not inaf_tag:
			obj_tag.create({
				'name': 'INAF',
				'applicability':'taxes',
				'active': True,
				'country_id':self.env.company.country_id.id,
				'record_sale':'3',
				'sequence': 12
			})

		exo_tag = obj_tag.search([('name','=','EXO')], limit=1)

		if not exo_tag:
			obj_tag.create({
				'name': 'EXO',
				'applicability':'taxes',
				'active': True,
				'country_id':self.env.company.country_id.id,
				'record_sale':'4',
				'sequence': 13
			})

		iscv_tag = obj_tag.search([('name','=','ISC-V')], limit=1)

		if not iscv_tag:
			obj_tag.create({
				'name': 'ISC-V',
				'applicability':'taxes',
				'active': True,
				'country_id':self.env.company.country_id.id,
				'record_sale':'5',
				'sequence': 14
			})

		otrosv_tag = obj_tag.search([('name','=','OTROS-V')], limit=1)

		if not otrosv_tag:
			obj_tag.create({
				'name': 'OTROS-V',
				'applicability':'taxes',
				'active': True,
				'country_id':self.env.company.country_id.id,
				'record_sale':'6',
				'sequence': 15
			})

		igvv_tag = obj_tag.search([('name','=','IGV-V')], limit=1)

		if not igvv_tag:
			obj_tag.create({
				'name': 'IGV-V',
				'applicability':'taxes',
				'active': True,
				'country_id':self.env.company.country_id.id,
				'record_sale':'7',
				'sequence': 16
			})

		ren4_tag = obj_tag.search([('name','=','RENTA 4TA')], limit=1)

		if not ren4_tag:
			obj_tag.create({
				'name': 'RENTA 4TA',
				'applicability':'taxes',
				'active': True,
				'country_id':self.env.company.country_id.id,
				'record_fees':'1',
				'sequence': 17
			})

		ret4_tag = obj_tag.search([('name','=','RET 4TA')], limit=1)

		if not ret4_tag:
			obj_tag.create({
				'name': 'RET 4TA',
				'applicability':'taxes',
				'active': True,
				'country_id':self.env.company.country_id.id,
				'record_fees':'2',
				'sequence': 18
			})

		perc_tag = obj_tag.search([('name','=','PER-C')], limit=1)

		if not perc_tag:
			obj_tag.create({
				'name': 'PER-C',
				'applicability':'taxes',
				'active': True,
				'country_id':self.env.company.country_id.id,
				'sequence': 19
			})

		icbper_c_tag = obj_tag.search([('name','=','ICBPER-C')], limit=1)

		if not icbper_c_tag:
			obj_tag.create({
				'name': 'ICBPER-C',
				'applicability':'taxes',
				'active': True,
				'country_id':self.env.company.country_id.id,
				'sequence': 20,
				'record_shop':'10'
			})

		icbper_v_tag = obj_tag.search([('name','=','ICBPER-V')], limit=1)

		if not icbper_v_tag:
			obj_tag.create({
				'name': 'ICBPER-V',
				'applicability':'taxes',
				'active': True,
				'country_id':self.env.company.country_id.id,
				'sequence': 21,
				'record_sale':'8'
			})

	def download_template(self):
		return {
			 'type' : 'ir.actions.act_url',
			 'url': '/web/binary/download_instructions_it',
			 'target': 'new',
			 }