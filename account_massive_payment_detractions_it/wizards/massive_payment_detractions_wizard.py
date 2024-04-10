# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError
import base64

from io import BytesIO
import re
import uuid

class MassivePaymentDetractionsWizard(models.TransientModel):
	_name = 'massive.payment.detractions.wizard'

	name = fields.Char()
	multipayment_id = fields.Many2one('multipayment.advance.it',string='Pago Multiple',required=True)
	type =  fields.Selection([('pc','Proveedor - Clientes'),('cp','Cliente - Proveedores')],string=u'Tipo',default='pc')

	def get_txt(self):
		ReportBase = self.env['report.base']
		lot_numer = self.multipayment_id.detraction_lot_number
		if not lot_numer:
			raise UserError(u'Es necesario llenar el campo Número de Lote de Detracciones en los Pagos Multiples Avanzados')
		ruc = self.multipayment_id.company_id.partner_id.vat

		if not ruc:
			raise UserError('No configuro el RUC de su Compañia.')

		#RUC + .tc
		name_doc = "D" + str(ruc) + lot_numer +".txt"
		sum_total = 0
		if self.type == 'cp':
			for i in self.multipayment_id.invoice_ids:
				sum_total += i.debe
		else:
			for i in self.multipayment_id.invoice_ids:
				sum_total += i.haber
		ctxt = "*" + str(ruc) + self.get_text_with_size(self.multipayment_id.company_id.partner_id.name,35,' ',True) + lot_numer + self.get_text_with_size(self.get_str_number(ReportBase.custom_round(sum_total)),15,'0',False)
		ctxt += """\r\n"""
		for elem in self.multipayment_id.invoice_ids:
			ctxt += '6' + (elem.partner_id.vat or '') + self.get_text_with_size(None,35,' ',True) + '000000000'
			code_operation = elem.good_services
			ctxt += self.get_text_with_size(code_operation,3,'0',False)
			acc_bank = self.env['res.partner.bank'].search([('partner_id','=',elem.partner_id.id),('is_detraction_account','=',True),'|',('company_id','=', elem.main_id.company_id.id),('company_id','=',False)],limit=1)
			if self.type == 'cp' and acc_bank.acc_number:
				ctxt += self.get_text_with_size(acc_bank.acc_number,11,' ',False)
			elif self.type == 'cp' and not acc_bank.acc_number:
				ctxt += self.get_text_with_size(None,11,' ',False)
			else:
				ctxt += ''
			ctxt += self.get_text_with_size(self.get_str_number(ReportBase.custom_round(elem.debe)),15,'0',False) if self.type == 'cp' else self.get_text_with_size(self.get_str_number(ReportBase.custom_round(elem.haber)),15,'0',False)
			type_op_det = elem.operation_type if elem.operation_type else '01'
			ctxt += type_op_det
			date = elem.invoice_id.move_id.invoice_date if elem.invoice_id.move_id.invoice_date else elem.invoice_id.move_id.date
			ctxt += str(date.year) + str('{:02d}'.format(date.month))
			ctxt += '01'
			partition = elem.invoice_id.nro_comp.split('-')
			ctxt += self.get_text_with_size(partition[0],4,'0',False) + self.get_text_with_size(partition[1],8,'0',False)
			ctxt += """\r\n"""

		import importlib
		import sys
		importlib.reload(sys)

		return self.env['popup.it'].get_file(name_doc,base64.encodebytes(b''+ctxt.encode("utf-8")))

	def get_text_with_size(self,text,size,complement,right):
		if not text:
			text = ''
		if len(text)<size:
			digits_number = ('').join((size-len(text))*[complement])
			if right:
				out = text + digits_number
			else:
				out = digits_number + text
		elif len(text)>size:
			out = text[:size] if right else text[len(text)-size:]
		else:
			out = text

		return out

	def get_str_number(self,number):
		a_float = round(number,2)
		cad = "{:.2f}".format(a_float).replace('.','')
		return str(cad)