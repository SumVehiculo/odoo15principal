# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.tools import float_round
import base64

class HrAutomateMultipayment(models.Model):
	_name = 'hr.automate.multipayment'
	_description = 'Hr Automate Multipayment'

	name = fields.Char(string='Nombre')
	journal_id = fields.Many2one('account.journal',string='Diario')
	payment_date = fields.Date(string='Fecha de pago')
	# catalog_payment_id = fields.Many2one('einvoice.catalog.payment',string='Medio de Pago')
	glosa = fields.Char(string='Glosa')
	tc = fields.Float(string='Tipo Cambio',digits=(12,3),default=1)
	state = fields.Selection([('draft','Borrador'),('done','Finalizado')],string='Estado',default='draft')
	company_id = fields.Many2one('res.company',string=u'Compañía',default=lambda self: self.env.company)

	payslip_run_id = fields.Many2one('hr.payslip.run', string='Periodo', domain=[('txt_generated', '=', False)], ondelete='cascade')
	slip_ids = fields.One2many('hr.payslip', 'multipayment_id', states={'done': [('readonly', True)]})
	gratification_id = fields.Many2one('hr.gratification', string='Gratificacion', domain=[('txt_generated', '=', False)], ondelete='cascade')
	grat_line_ids = fields.One2many('hr.gratification.line', 'multipayment_id', states={'done': [('readonly', True)]})
	cts_id = fields.Many2one('hr.cts', string='CTS', domain=[('txt_generated', '=', False)], ondelete='cascade')
	cts_line_ids = fields.One2many('hr.cts.line', 'multipayment_id', states={'done': [('readonly', True)]})
	cts_dollars = fields.Boolean(string='CTS Dolares', default=False)

	is_hr_payment = fields.Boolean(string='Es pago de Recursos Humanos')
	# is_biweekly_advance = fields.Boolean(string='Es pago quincenal', default=False)
	format_bank = fields.Selection(related='journal_id.bank_id.format_bank')

	####BBVA####
	process_type = fields.Selection([
		('A', 'Inmediato'),
		('H', 'Hora de Proceso'),
		('F', 'Fecha Futura'),
	], string='Tipo de Proceso', default='A')
	process_hour = fields.Selection([
		('B', '11:00 a.m.'),
		('C', '03:00 p.m.'),
		('D', '07:00 p.m.'),
	], string='Hora de Proceso')
	owner_validation = fields.Selection([
		('S', 'Valida, si hay error rechaza el abono'),
		('N', 'No valida'),
	], string='Validacion de Pertenencia', default='S')
	alert_indicator = fields.Selection([
		('E', 'Email'),
		('C', 'Celular'),
	], string='Indicador de Aviso', default='')

	####BCP####
	flag = fields.Boolean(string='La cuenta de abono pertenece al titular de la cuenta origen', default=False)
	idc_flag = fields.Boolean(string='Desea validar IDC vs Cuenta', default=True)
	subtype = fields.Selection([
		('G', 'Gratificacion'),
		('V', 'Vacaciones'),
		('M', 'Movilidad'),
		('P', 'Pensionista'),
		('T', 'Prestamos'),
		('4', 'Cuarta Categoria'),
		('O', 'Otros Afectos'),
		('X', 'Quinta Categoria'),
		('Z', 'Otros Inafectos'),
	], string='Subtipo de Planilla Haberes', default='O', required=True)

	####INTERBANK####
	company_code = fields.Char(string='Codigo de la Empresa', default='EE01')
	service_code = fields.Char(string='Codigo del Servicio', default='01')
	process_type_interbank = fields.Selection([
		('0', 'En Linea'),
		('1', 'En Diferido'),
	], string='Tipo de Proceso', default='0')
	person_type = fields.Selection([
		('P', 'Persona Natural'),
		('C', 'Comercial o Juridica'),
	], string='Tipo de Persona', default='C')

	####SCOTIABANK####
	charge_way = fields.Selection([
		('1', 'Cargo en Cuenta'),
		('2', 'Cobro por Cajero, Ventanilla o Medios Virtuales'),
		('5', 'Afiliado a Planilla'),
		('6', 'Desafiliado a Planilla'),
	], string='Modalidad de Cobro', default='1')
	charge_type = fields.Selection([
		('DU', 'Urgencia'),
		('NO', 'Normal'),
	], default='DU', string='Tipo de Abono')
	payment_way = fields.Selection([
		('2', 'Abono Cuenta Cte.'),
		('3', 'Abono Cuenta Ahorro'),
		('4', 'Abono CCI'),
	], string='Forma de Pago', default='3')

	####banbif#####
	bb_currency=[
		('PEN','1'),
		('USD','2')]

	bb_doctype=[
		('DNI','1'),
		('CE','3'),
		('LM','4')]

	bb_motdep=[
		('CTS','0'),
		('HABERES4','4'),
		('HABERES5','5'),
		('OHG','8'),
		('OHE','9')]

	subtypebanbif = fields.Selection([
		('4', 'Cuarta Categoria'),
		('5', 'Quinta Categoria'),
	], string='Subtipo de Planilla Haberes', default='5', required=True)


	@api.model
	def create(self, vals):
		id_seq = self.env['ir.sequence'].search([('name', '=', 'Pagos Multiples Planillas'),('company_id','=',self.env.company.id)],limit=1)
		if not id_seq:
			id_seq = self.env['ir.sequence'].create({'name': 'Pagos Multiples Planillas', 'company_id': self.env.company.id, 'implementation': 'no_gap','active': True, 'prefix': 'PM-', 'padding': 6, 'number_increment': 1, 'number_next_actual': 1})
		vals['name'] = id_seq._next()
		t = super(HrAutomateMultipayment, self).create(vals)
		return t

	def delete_special_chars(self, _string):
		import string
		normal_chars = list(string.ascii_letters)
		normal_chars += list(string.digits)
		normal_chars.append(' ')
		special_chars = {
			'Ñ': 'N', 'ñ': 'n', 'Á': 'A', 'É': 'E', 'Í': 'I', 'Ó': 'O', 'Ú': 'U', 'á': 'a', 'é': 'e', 'í': 'i',
			'ó': 'o', 'ú': 'u', 'Ü': 'U', 'ü': 'u', '@': 'a', ':': '', 'Ã': 'A', '`': '', '“': '',
		}
		new_str = _string
		for l in _string:
			if l in special_chars.keys():
				new_str = new_str.replace(l, special_chars[l])
			elif l not in normal_chars:
				new_str = new_str.replace(l, '')
		return new_str

	@api.onchange('payslip_run_id', 'journal_id')
	def get_slip_ids(self):
		for rec in self:
			if rec.payslip_run_id and rec.payslip_run_id.slip_ids and rec.journal_id:
				Slips = rec.payslip_run_id.slip_ids.filtered(lambda l: l.wage_bank.format_bank == rec.format_bank)
				rec.slip_ids = [(6, 0, Slips.ids)]

	@api.onchange('cts_id', 'journal_id')
	def get_cts_line_ids(self):
		for rec in self:
			if rec.cts_id and rec.cts_id.line_ids and rec.journal_id:
				cts_lines = rec.cts_id.line_ids.filtered(lambda l: l.cts_bank.format_bank == rec.journal_id.bank_id.format_bank and l.cts_id.company_id.id == rec.journal_id.company_id.id)
				rec.cts_line_ids = [(6, 0, cts_lines.ids)]

	@api.onchange('gratification_id', 'journal_id')
	def get_grat_line_ids(self):
		for rec in self:
			if rec.gratification_id and rec.gratification_id.line_ids and rec.journal_id:
				grat_lines = rec.gratification_id.line_ids.filtered(lambda l: l.wage_bank.format_bank == rec.journal_id.bank_id.format_bank and l.gratification_id.company_id.id == rec.journal_id.company_id.id)
				rec.grat_line_ids = [(6, 0, grat_lines.ids)]

	def procesing_payments(self):
		if not self.payslip_run_id and not self.cts_id:
			raise UserError('Para finalizar debe tener al menos un periodo o una cts seleccionado')
		if self.payslip_run_id:
			self.payslip_run_id.txt_generated = True
		if self.cts_id:
			self.cts_id.txt_generated = True
		if self.gratification_id:
			self.gratification_id.txt_generated = True
		self.state = 'done'

	def turn_draft(self):
		if self.payslip_run_id:
			self.payslip_run_id.txt_generated = False
		if self.cts_id:
			self.cts_id.txt_generated = False
		if self.gratification_id:
			self.gratification_id.txt_generated = False
		self.state = 'draft'

	def check_account_type(self, BankAccount, bank):
		log = ''
		if not BankAccount.currency_id:
			log += 'No se ha especificado una moneda en la cuenta %s\n' % BankAccount.acc_number
		elif not BankAccount.type_of_account:
			log += 'No se ha especificado un tipo de cuenta en la cuenta %s\n' % BankAccount.acc_number
		elif BankAccount.type_of_account and BankAccount.type_of_account not in ['0', '1', '3']:
			log += 'La cuenta %s tiene un tipo de cuenta diferente a Corriente, Ahorros o Interbancaria\n' % BankAccount.acc_number

		if BankAccount.type_of_account == '3' and len(BankAccount.acc_number) != 20:
			log += 'La cuenta %s debe tener 20 digitos\n' % BankAccount.acc_number

		if bank == 'bbva':
			if BankAccount.branch_name:
				account = BankAccount.acc_number[:8] + BankAccount.branch_name + BankAccount.acc_number[8:]
			else:
				account = BankAccount.acc_number
			if BankAccount.type_of_account in ['0', '1'] and len(account) != 20:
				log += 'La cuenta %s debe tener 20 digitos\n' % BankAccount.acc_number
		elif bank == 'bcp':
			if BankAccount.type_of_account == '0' and len(BankAccount.acc_number) != 13:
				log += 'La cuenta %s debe tener 13 digitos\n' % BankAccount.acc_number
			if BankAccount.type_of_account == '1' and len(BankAccount.acc_number) != 14:
				log += 'La cuenta %s debe tener 14 digitos\n' % BankAccount.acc_number
		elif bank == 'interbank':
			if BankAccount.type_of_account in ['0', '1'] and len(BankAccount.acc_number) != 13:
				log += 'La cuenta %s debe tener 13 digitos\n' % BankAccount.acc_number
		elif bank == 'scotiabank':
			if BankAccount.type_of_account in ['0', '1'] and len(BankAccount.acc_number) > 14:
				log += 'La cuenta %s debe tener menos de 14 digitos\n' % BankAccount.acc_number
		# elif bank == 'banbif':
		# 	if BankAccount.type_of_account in ['0', '1'] and len(BankAccount.acc_number) != 20:
		# 		log += 'La cuenta %s debe tener 20 digitos\n' % BankAccount.acc_number
		return log

	def parse_to_txt(self, var, type, range=1, left=True, decimal_point=False):
		'''Analizar el tipo de dato int, str, float, date or datetime para el formato txt
		:param var: The variable that you wan't to parse
		:param type: The type of the var that you are using
		:param range: The space that are going to refill with the text
		:param left: The direction of the space that you are using, if you send False the space will turn to right
		:param decimal_point: The decimal point of the float var will be print in the txt
		:return: The plain text for the txt file
		'''
		if type not in ['date', 'datetime'] and len(str(var)) > range:
			var = str(var)[0:range]
		spacer = ' ' if type == 'str' or type=='txt' else '0'

		aux = spacer * range
		# print(12312,var,type,spacer,aux)
		if type in ['int', 'str']:
			var = str(var)
			var = var.replace('ñ', 'n')
			var = var.replace('Ñ', 'N')
			var = self.delete_special_chars(var)
			if left:
				res = var + aux[len(var):]
			else:
				res = aux[:-len(var)] + var
		elif type == 'float':
			var = self.env['report.base'].custom_round(var, 2)
			Lang = self.env['res.lang'].search([('active', '=', True)], limit=1)
			var = str(var).split(Lang.decimal_point)
			dp = Lang.decimal_point if decimal_point else ''
			if len(var[1]) == 1:
				var[1] += '0'
			if left:
				res = var[0] + dp + var[1] + aux[len(var[0] + dp + var[1]):]
			else:
				res = aux[:-len(var[0] + dp + var[1])] + var[0] + dp + var[1]
		elif type == 'date':
			aux = '00'
			year, month, day = str(var.year), str(var.month), str(var.day)
			res = year + aux[:-len(month)] + month + aux[:-len(day)] + day
		elif type == 'datetime':
			import pytz
			aux = '00'
			if not self.env.user.partner_id.tz:
				raise UserError(
					'Es necesario que configure la zona horaria en el partner del usuario que esta utilizando')
			tz = pytz.timezone(self.env.user.partner_id.tz)
			date_tz = pytz.utc.localize(var).astimezone(tz)
			year, month, day = str(date_tz.year), str(date_tz.month), str(date_tz.day)
			hour, minute, second = str(date_tz.hour), str(date_tz.minute), str(date_tz.second)
			res = year + aux[:-len(month)] + month + aux[:-len(day)] + day + \
				  aux[:-len(hour)] + hour + aux[:-len(minute)] + minute + aux[:-len(second)] + second
		elif type == 'txt':
			if left:
				res = var + aux[len(var):]
			else:
				res = aux[:-len(var)] + var
		return res

	# PAGO DE HABERES
	def get_hr_txt(self):
		if not self.journal_id.bank_account_id:
			raise UserError('El diario seleccionado no tiene una cuenta bancaria definida')
		if self.format_bank == 'bbva':
			self.verify_bbva_hr_fields()
			return self.get_bbva_hr_txt(gratification=self._context.get('gratification'))
		elif self.format_bank == 'bcp':
			self.verify_bcp_hr_fields()
			return self.get_bcp_hr_txt(gratification=self._context.get('gratification'))
		elif self.format_bank == 'interbank':
			self.verify_interbank_hr_fields()
			return self.get_interbank_hr_txt(gratification=self._context.get('gratification'))
		elif self.format_bank == 'scotiabank':
			self.verify_scotiabank_hr_fields()
			return self.get_scotiabank_hr_txt_2(gratification=self._context.get('gratification'))
		elif self.format_bank == 'banbif':
			self.verify_banbif_hr_fields()
			return self.get_banbif_hr_txt(gratification=self._context.get('gratification'))
		else:
			raise UserError('El diario no tiene un banco con formato definido')

	def verify_bbva_hr_fields(self):
		log = ''
		BankAccount = self.journal_id.bank_account_id
		if not BankAccount.branch_name:
			raise UserError('No se ha especificado una sucursal en la cuenta del banco')
		log += self.check_account_type(BankAccount, 'bbva')
		if BankAccount.type_of_account == '3':
			log += 'No se puede utilizar la cuenta %s de tipo interbancaria como cuenta de cargo\n' % BankAccount.acc_number
		if not self.process_type:
			log += 'Necesita especificar un tipo de proceso\n'
		for line in self.slip_ids:
			if not line.employee_id.type_document_id.bbva_code:
				log += 'El tipo de documento del partner %s no tiene su codigo BBVA\n' % line.employee_id.name
			if not line.employee_id.identification_id:
				log += 'El partner %s no tiene un numero de documento asignado\n' % line.employee_id.name
			PartnerAccount = line.employee_id.wage_bank_account_id
			log += self.check_account_type(PartnerAccount, 'bbva')
		if log:
			raise UserError('Se han detectado los siguientes errores\n' + log)

	def verify_bcp_hr_fields(self):
		log = ''
		BankAccount = self.journal_id.bank_account_id
		log += self.check_account_type(BankAccount, 'bcp')
		if BankAccount.type_of_account == '3':
			log += 'No se puede utilizar la cuenta %s de tipo interbancaria como cuenta de cargo\n' % BankAccount.acc_number
		for line in self.slip_ids:
			if not line.employee_id.type_document_id.bcp_code:
				log += 'El tipo de documento del partner %s no tiene su codigo BCP\n' % line.employee_id.name
			if not line.employee_id.identification_id:
				log += 'El partner %s no tiene un numero de documento asignado\n' % line.employee_id.name
			PartnerAccount = line.employee_id.wage_bank_account_id
			log += self.check_account_type(PartnerAccount, 'bcp')
		if log:
			raise UserError('Se han detectado los siguientes errores\n' + log)

	def verify_interbank_hr_fields(self):
		log = ''
		BankAccount = self.journal_id.bank_account_id
		log += self.check_account_type(BankAccount, 'interbank')
		if BankAccount.type_of_account == '3':
			log += 'No se puede utilizar la cuenta %s de tipo interbancaria como cuenta de cargo\n' % BankAccount.acc_number
		if not self.company_code:
			log += 'El codigo de compañia es un campo obligatorio\n'
		if not self.service_code:
			log += 'El codigo de servicio es un campo obligatorio\n'
		if not self.process_type_interbank:
			log += 'El tipo de proceso es un campo obligatorio\n'
		if not self.person_type:
			log += 'El tipo de persona es un campo obligatorio\n'
		for line in self.slip_ids:
			if not line.employee_id.type_document_id.interbank_code:
				log += 'El tipo de documento del partner %s no tiene su codigo Interbank\n' % line.employee_id.name
			if not line.employee_id.identification_id:
				log += 'El partner %s no tiene un numero de documento asignado\n' % line.employee_id.name
			PartnerAccount = line.employee_id.wage_bank_account_id
			log += self.check_account_type(PartnerAccount, 'interbank')
		if log:
			raise UserError('Se han detectado los siguientes errores\n' + log)

	def verify_scotiabank_hr_fields(self):
		log = ''
		BankAccount = self.journal_id.bank_account_id
		log += self.check_account_type(BankAccount, 'scotiabank')
		if not self.charge_way:
			log += 'La Modalidad de Cobro es un campo obligatorio\n'
		for line in self.slip_ids:
			PartnerAccount = line.employee_id.wage_bank_account_id
			log += self.check_account_type(PartnerAccount, 'scotiabank')

	def verify_banbif_hr_fields(self):
		log = ''
		for line in self.slip_ids:
			if not line.employee_id.type_document_id.banbif_code:
				log += 'El tipo de documento del partner %s no tiene su codigo BanBif\n' % line.employee_id.name
			if not line.employee_id.identification_id:
				log += 'El partner %s no tiene un numero de documento asignado\n' % line.employee_id.name
			PartnerAccount = line.employee_id.wage_bank_account_id
			log += self.check_account_type(PartnerAccount, 'banbif')
		if log:
			raise UserError('Se han detectado los siguientes errores\n' + log)

	def get_amounts_total_hr(self, gratification):
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		MainParameter.check_gratification_values()
		if gratification:
			# Gratification = self.env['hr.gratification'].search([('payslip_run_id', '=', self.payslip_run_id.id)])
			Gratification = self.gratification_id
			Lines = Gratification.line_ids.filtered(lambda l: l.employee_id in self.grat_line_ids.mapped('employee_id') and l.is_text == True)
			return sum(Lines.mapped('total'))
		else:
			amounts = []
			for slip in self.slip_ids.filtered(lambda l: l.is_text == True):
				# if self.is_biweekly_advance:
				#	 amounts.append(self.env['report.base'].custom_round(slip.biweekly_advance, 2))
				# else:
				amounts.append(self.env['report.base'].custom_round(slip.net_to_pay, 2))
			return sum(amounts)

	def get_amount_to_pay(self, line, gratification):
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		MainParameter.check_gratification_values()
		if gratification:
			# Gratification = self.env['hr.gratification'].search([('payslip_run_id', '=', self.payslip_run_id.id)])
			Gratification = self.gratification_id
			Line = Gratification.line_ids.filtered(lambda l: l.employee_id == line.employee_id)
			return Line.total
		else:
			# if self.is_biweekly_advance:
			#	 return line.biweekly_advance
			# else:
			return line.net_to_pay


	def get_bbva_hr_txt(self, gratification=False):
		MainParameter = self.env['hr.main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
		if not MainParameter or not MainParameter.dir_create_file:
			raise UserError(u'No existe un Directorio de Descarga configurado en Parametros Principales de Nomina para su Compañía')
		doc_name = '%sBBVA_Haberes.txt' % MainParameter.dir_create_file
		f = open(doc_name, 'w+')
		BankAccount = self.journal_id.bank_account_id
		acc_number = BankAccount.acc_number[:8] + BankAccount.branch_name + BankAccount.acc_number[8:]
		amounts_total = self.get_amounts_total_hr(gratification)
		if gratification:
			slip_ids = self.grat_line_ids.filtered(lambda l: l.is_text == True)
		else:
			slip_ids = self.slip_ids.filtered(lambda l: l.is_text == True)

		f.write('700{account}{currency}{total}{process}{date}{hour}{reference}{lines}{valid}{cero}'.format(
			account=acc_number,
			currency=BankAccount.currency_id.name,
			total=self.parse_to_txt(amounts_total, 'float', range=15, left=False),
			process=self.process_type,
			date=self.parse_to_txt(self.payment_date, 'date') if self.process_type == 'F' else ' ' * 8,
			hour=self.process_hour if self.process_type == 'H' else ' ',
			reference=self.parse_to_txt(self.glosa, 'str', range=25) if self.glosa else ' ' * 25,
			lines=self.parse_to_txt(len(slip_ids), 'int', range=6, left=False),
			valid=self.owner_validation,
			cero='0' * 18,
		) + ' ' * 50 + '\r\n')
		# als=[]
		# for l in slip_ids:
		# 	als.append(l.id)

		# for line in slip_ids.search([('id','in',als)],order='name'):
		for line in slip_ids:
			PartnerAccount = line.employee_id.wage_bank_account_id
			if self.alert_indicator == 'E':
				alert_val = line.employee_id.work_email or ''
			elif self.alert_indicator == 'C':
				alert_val = line.employee_id.work_phone or ''
			else:
				alert_val = ''
			amount_to_pay = self.get_amount_to_pay(line, gratification)
			if amount_to_pay>0:
				f.write('002{p_doc_type}{p_doc_num}{charge_type}{payment_doc}{beneficiary_name}{amount}\
{reference}{alert_indicator}{alert_val}'.format(
					p_doc_type=line.employee_id.type_document_id.bbva_code,
					p_doc_num=self.parse_to_txt(line.employee_id.identification_id, 'str', range=12),
					charge_type='I' if PartnerAccount.type_of_account == '3' else 'P',
					payment_doc=self.parse_to_txt(PartnerAccount.acc_number, 'str', range=20),
					beneficiary_name=self.parse_to_txt(line.employee_id.name, 'str', range=40),
					amount=self.parse_to_txt(amount_to_pay, 'float', range=15, left=False),
					reference=self.parse_to_txt(line.employee_id.identification_id if gratification else line.number, 'str', range=40),
					alert_indicator=self.alert_indicator if self.alert_indicator else ' ',
					alert_val=self.parse_to_txt(alert_val, 'str', range=50),
				) + ' ' * 50 + '\r\n')
		f.close()
		f = open(doc_name, 'rb')
		return self.env['popup.it'].get_file('BBVA_Haberes.txt', base64.encodebytes(b''.join(f.readlines())))

	def get_bcp_hr_txt(self, gratification=False):
		MainParameter = self.env['hr.main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
		if not MainParameter or not MainParameter.dir_create_file:
			raise UserError(u'No existe un Directorio de Descarga configurado en Parametros Principales de Nomina para su Compañía')
		doc_name = '%sBCP_Haberes.txt' % MainParameter.dir_create_file
		f = open(doc_name, 'w+')
		BankAccount = self.journal_id.bank_account_id
		ACCOUNT_TYPE = {'0': 'C', '1': 'A', '3': 'B'}

		if gratification:
			slip_ids = self.grat_line_ids.filtered(lambda l: l.is_text == True)
		else:
			slip_ids = self.slip_ids.filtered(lambda l: l.is_text == True)

		acc_numbers = []
		numpag=0
		for i in slip_ids:
			amount_to_pay = self.get_amount_to_pay(i, gratification)
			if amount_to_pay>0:
				PartnerAccount = i.employee_id.wage_bank_account_id
				if PartnerAccount.type_of_account == '3':
					acc_numbers.append(int(PartnerAccount.acc_number[10:]))
				else:
					acc_numbers.append(int(PartnerAccount.acc_number[3:]))
				numpag=numpag+1

		acc_numbers.append(int(BankAccount.acc_number[3:]))
		check_sum = sum(acc_numbers)
		amounts_total = self.get_amounts_total_hr(gratification)
		cs=str(check_sum).strip().rjust(15,'0')
		f.write('1{lines}{date}{subtype}{charge_type}{currency}{account}{total}{reference}{check_sum}\r\n'.format(
			lines=self.parse_to_txt(numpag, 'int', range=6, left=False),
			date=self.parse_to_txt(self.payment_date, 'date'),
			subtype=self.subtype,
			charge_type='C',
			currency='0001' if BankAccount.currency_id.name == 'PEN' else '1001',
			account=self.parse_to_txt(BankAccount.acc_number, 'str', range=20),
			total=self.parse_to_txt(amounts_total, 'float', range=17, left=False, decimal_point=True),
			reference=self.parse_to_txt(self.glosa, 'str', range=40),
			check_sum=cs,
			#check_sum=self.parse_to_txt(str(check_sum), 'str', range=15,left=True, decimal_point=False),
		))
		# als=[]
		# for l in slip_ids:
		# 	als.append(l.id)

		# for line in slip_ids.search([('id','in',als)],order='name'):
		for line in slip_ids:
			PartnerAccount = line.employee_id.wage_bank_account_id
			amount_to_pay = self.get_amount_to_pay(line, gratification)
			if amount_to_pay>0:
				f.write('2{account_type}{payment_doc}{p_doc_type}{p_doc_num}   {beneficiary_name}\
{beneficiary_ref}{company_ref}{currency}{amount}{flag}\r\n'.format(
					account_type=ACCOUNT_TYPE.get(PartnerAccount.type_of_account, ' '),
					payment_doc=self.parse_to_txt(PartnerAccount.acc_number, 'str', range=20),
					p_doc_type=line.employee_id.type_document_id.bcp_code,
					p_doc_num=self.parse_to_txt(line.employee_id.identification_id, 'str', range=12),
					beneficiary_name=self.parse_to_txt(line.employee_id.name, 'str', range=75),
					beneficiary_ref=self.parse_to_txt(line.employee_id.identification_id if gratification else line.number, 'str', range=40),
					company_ref=self.parse_to_txt(self.env.company.name, 'str', range=20),
					currency='0001' if BankAccount.currency_id.name == 'PEN' else '1001',
					amount=self.parse_to_txt(amount_to_pay, 'float', range=17, left=False, decimal_point=True),
					flag='S' if self.idc_flag else 'N',
				))
		f.close()
		f = open(doc_name, 'rb')
		return self.env['popup.it'].get_file('BCP_Haberes.txt', base64.encodebytes(b''.join(f.readlines())))

	def get_interbank_hr_txt(self, gratification=False):
		MainParameter = self.env['hr.main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
		if not MainParameter or not MainParameter.dir_create_file:
			raise UserError(u'No existe un Directorio de Descarga configurado en Parametros Principales de Nomina para su Compañía')
		doc_name = '%sInterbank_Haberes.txt' % MainParameter.dir_create_file
		f = open(doc_name, 'w+')
		BankAccount = self.journal_id.bank_account_id
		after_date = fields.Date.today() if self.process_type_interbank == '0' else self.payment_date
		amounts_total = self.get_amounts_total_hr(gratification)
		if gratification:
			slip_ids = self.grat_line_ids.filtered(lambda l: l.is_text == True)
		else:
			slip_ids = self.slip_ids.filtered(lambda l: l.is_text == True)
# 		f.write('0104{company}{service}{account}{type_account}{currency}{reference}{date}{process_type}\
# {after_date}{lines}{soles_total}{usd_total}MC001\r\n'.format(
# 			company=self.parse_to_txt(self.company_code, 'str', range=4),
# 			service=self.parse_to_txt(self.service_code, 'str', range=2),
# 			account=self.parse_to_txt(BankAccount.acc_number, 'str', range=13),
# 			type_account='001' if BankAccount.type_of_account == '0' else '002',
# 			currency='01' if BankAccount.currency_id.name == 'PEN' else '10',
# 			reference=self.parse_to_txt(self.glosa, 'str', range=12),
# 			date=self.parse_to_txt(fields.Datetime.now(), 'datetime'),
# 			process_type=self.process_type_interbank,
# 			after_date=self.parse_to_txt(after_date, 'date'),
# 			lines=self.parse_to_txt(len(self.slip_ids), 'int', range=6),
# 			soles_total=self.parse_to_txt(amounts_total, 'float',
# 										  range=15) if BankAccount.currency_id.name == 'PEN' else '0' * 15,
# 			usd_total=self.parse_to_txt(amounts_total, 'float',
# 										range=15) if BankAccount.currency_id.name == 'USD' else '0' * 15,
# 		))

		f.write('0104{espacios}{date}{espacios2}{lines}{soles_total}{usd_total}MC001\r\n'.format(
			espacios=' '*36,
			date=self.parse_to_txt(fields.Datetime.now(), 'datetime'),
			espacios2=' '*9,
			lines=self.parse_to_txt(len(slip_ids), 'int', left=False,range=6),
			soles_total=self.parse_to_txt(amounts_total, 'float',left=False,range=15) if BankAccount.currency_id.name == 'PEN' else '0' * 15,
			usd_total=self.parse_to_txt(amounts_total, 'float',	range=15) if BankAccount.currency_id.name == 'USD' else '0' * 15,
		))
		# als=[]
		# for l in self.slip_ids:
		# 	als.append(l.id)
		#
		# for line in self.slip_ids.search([('id','in',als)],order='name'):
		for line in slip_ids:
			PartnerAccount = line.employee_id.wage_bank_account_id
			ACCOUNT_TYPE = {'0': '001', '1': '002', '3': ' ' * 3}
			if self.person_type == 'P':
				benef_name = self.parse_to_txt(line.employee_id.last_name or '', 'str', range=20) + \
							 self.parse_to_txt(line.employee_id.m_last_name or '', 'str', range=20) + \
							 self.parse_to_txt(line.employee_id.names or '', 'str', range=20)
			else:
				benef_name = self.parse_to_txt(line.employee_id.name, 'str', range=60)
			amount_to_pay = self.get_amount_to_pay(line, gratification)
			email=line.employee_id.work_email or ''

			if amount_to_pay>0:
# 				f.write('02{doc_type}{benef_code}{doc_number}{date_to}{charge_currency}{amount} {charge_type}{account_type}\
# {account_currency}{account_office}{acc_number}{person_type}{p_doc_type}{p_doc_num}{benef_name}{currency_cts}{amount_cts}\
# {filler}{cell_phone}{email}\r\n'.format(
# 					doc_type=line.employee_id.type_document_id.interbank_code,
# 					benef_code=self.parse_to_txt(line.employee_id.identification_id, 'str', range=20),
# 					#doc_type=' ',
# 					doc_number=' ' * 19,
# 					date_to=' ' * 8,
# 					charge_currency='01' if BankAccount.currency_id.name == 'PEN' else '10',
# 					amount=self.parse_to_txt(amount_to_pay, 'float', left=False,range=15),
# 					charge_type='99' if PartnerAccount.type_of_account == '3' else '09',
# 					account_type=ACCOUNT_TYPE.get(PartnerAccount.type_of_account, ' ' * 3),
# 					account_currency=' ' * 2 if PartnerAccount.type_of_account == '3' else (
# 						'01' if BankAccount.currency_id.name == 'PEN' else '10'),
# 					account_office=' ' * 3 if PartnerAccount.type_of_account == '3' else PartnerAccount.acc_number[:3],
# 					acc_number=PartnerAccount.acc_number if PartnerAccount.type_of_account == '3' \
# 						else self.parse_to_txt(PartnerAccount.acc_number[:3], 'str', range=20),
# 					person_type=self.person_type if self.person_type else ' ',
# 					p_doc_type=line.employee_id.type_document_id.interbank_code,
# 					p_doc_num=self.parse_to_txt(line.employee_id.identification_id, 'str', range=15),
# 					benef_name=benef_name,
# 					currency_cts=' ' * 2,
# 					amount_cts=' ' * 15,
# 					filler=' ' * 6,
# 					cell_phone=self.parse_to_txt(line.employee_id.work_phone or '', 'str', range=40),
# 					email=self.parse_to_txt(line.employee_id.work_email or '', 'str', range=140),
# 				))

				f.write('02{doc_type}{benef_code}{doc_number}{date_to}{charge_currency}{amount} {charge_type}{account_type}\
{account_currency}{acc_number}{person_type}{p_doc_type}{p_doc_num}{benef_name}{currency_cts}{amount_cts}\
{filler}{cell_phone}{email}\r\n'.format(
					doc_type=line.employee_id.type_document_id.interbank_code,
					benef_code=self.parse_to_txt(line.employee_id.identification_id, 'str', range=20),
					#doc_type=' ',
					doc_number=' ' * 19,
					date_to=' ' * 8,
					charge_currency='01' if BankAccount.currency_id.name == 'PEN' else '10',
					amount=self.parse_to_txt(amount_to_pay, 'float', left=False,range=15),
					charge_type='99' if PartnerAccount.type_of_account == '3' else '09',
					account_type=ACCOUNT_TYPE.get(PartnerAccount.type_of_account, ' ' * 3),
					account_currency=' ' * 2 if PartnerAccount.type_of_account == '3' else ('01' if BankAccount.currency_id.name == 'PEN' else '10'),
					acc_number= (' ' * 3)+self.parse_to_txt(PartnerAccount.acc_number, 'str', range=20) if PartnerAccount.type_of_account == '3' else self.parse_to_txt(PartnerAccount.acc_number, 'str', range=23),
					person_type=self.person_type if self.person_type else ' ',
					p_doc_type=line.employee_id.type_document_id.interbank_code,
					p_doc_num=self.parse_to_txt(line.employee_id.identification_id, 'str', range=15),
					benef_name=benef_name,
					currency_cts=' ' * 2,
					amount_cts='0' * 15,
					filler=' ' * 6,
					cell_phone=' '*40,
					email=' '*140,

				))
		f.close()
		f = open(doc_name, 'rb')
		return self.env['popup.it'].get_file('Interbank_Haberes.txt', base64.encodebytes(b''.join(f.readlines())))

	def get_scotiabank_hr_txt(self, gratification=False):
		MainParameter = self.env['hr.main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
		if not MainParameter or not MainParameter.dir_create_file:
			raise UserError(u'No existe un Directorio de Descarga configurado en Parametros Principales de Nomina para su Compañía')
		doc_name = '%sScotiabank_Haberes.txt' % MainParameter.dir_create_file
		f = open(doc_name, 'w+')
		BankAccount = self.journal_id.bank_account_id
		DOC_TYPE = {'1': '01', '4': '02'}
		if gratification:
			slip_ids = self.grat_line_ids.filtered(lambda l: l.is_text == True)
		else:
			slip_ids = self.slip_ids.filtered(lambda l: l.is_text == True)
		# als=[]
		# for l in self.slip_ids:
		# 	als.append(l.id)
		#
		# for line in self.slip_ids.search([('id','in',als)],order='name'):
		for line in slip_ids:
			PartnerAccount = line.employee_id.wage_bank_account_id
			# percent = self.env['report.base'].custom_round((line.net_discounts * 100)/line.biweekly_advance if self.is_biweekly_advance else line.net_to_pay, 4)
			amount_to_pay = self.get_amount_to_pay(line, gratification)
			if amount_to_pay>0:
				f.write('{doc_number}{service_type}{bank_code}{employee_code}{employee_name}{situation}{company_code}\
	{percent}{amount_1}{amount_2}{amount_3}{amount_4}{amount_5}{amount_6}{acc_number}{whites}{charge}{charge_acc}{employee_doc}\
	{employee_num}{user_name}{date}{inter_acc_number}\r\n'.format(
					doc_number=self.parse_to_txt(self.env.company.vat, 'str', range=11),
					service_type='20' if BankAccount.currency_id.name == 'PEN' else '21',
					bank_code=' ' * 10,
					employee_code=self.parse_to_txt(line.employee_id.identification_id, 'str', range=10),
					employee_name=self.parse_to_txt(line.employee_id.name, 'str', range=30),
					situation='2' if line.contract_id.situation_id.code == '0' else '1',
					company_code=' ' * 8,
					# percent = self.parse_to_txt(percent, 'float', range=6, decimal_point=True),
					percent='0.0000',
					amount_1=self.parse_to_txt(amount_to_pay, 'float', range=10, decimal_point=True, left=False),
					amount_2='0000000.00',
					amount_3='0000000.00',
					amount_4='0000000.00',
					amount_5='0000000.00',
					amount_6='0000000.00',
					acc_number=self.parse_to_txt(PartnerAccount.acc_number if PartnerAccount.type_of_account in ['0', '1'] else '', 'str', range=14),
					whites=' ' * 16,
					charge=self.charge_way,
					charge_acc=self.parse_to_txt(BankAccount.acc_number, 'str', range=14),
					employee_doc=DOC_TYPE.get(line.employee_id.type_document_id.sunat_code, ' ' * 2),
					employee_num=self.parse_to_txt(line.employee_id.identification_id.strip(), 'str', range=12),
					user_name=self.parse_to_txt(self.env.user.name, 'str', range=30),
					date=self.parse_to_txt(self.payment_date, 'date'),
					inter_acc_number=self.parse_to_txt(PartnerAccount.acc_number if PartnerAccount.type_of_account == '3' else '', 'str', range=20),
				))
		f.close()
		f = open(doc_name, 'rb')
		return self.env['popup.it'].get_file('Scotiabank_Haberes.txt', base64.encodebytes(b''.join(f.readlines())))

	def get_scotiabank_hr_txt_2(self, gratification=False):
		MainParameter = self.env['hr.main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
		if not MainParameter or not MainParameter.dir_create_file:
			raise UserError(u'No existe un Directorio de Descarga configurado en Parametros Principales de Nomina para su Compañía')
		doc_name = '%sScotiabank_Haberes.txt' % MainParameter.dir_create_file
		f = open(doc_name, 'w+')
		BankAccount = self.journal_id.bank_account_id
		DOC_TYPE = {'1': '1', '4': '2', '7': '3'}
		if gratification:
			slip_ids = self.grat_line_ids.filtered(lambda l: l.is_text == True)
		else:
			slip_ids = self.slip_ids.filtered(lambda l: l.is_text == True)

		for line in slip_ids:
			PartnerAccount = line.employee_id.wage_bank_account_id
			amount_to_pay = self.get_amount_to_pay(line, gratification)
			if amount_to_pay>0:
				f.write(
					'{doc_type}{doc_number}{employee_name}{payment_way}{acc_number}{acc_number_cci}{amount}{labor_regime}{currency}{concept}{payment_type}\r\n'.format(
						doc_type=DOC_TYPE.get(line.employee_id.type_document_id.sunat_code, ' '),
						doc_number=self.parse_to_txt(line.employee_id.identification_id.strip(), 'str', range=12),
						employee_name=self.parse_to_txt(line.employee_id.name, 'str', range=60),
						payment_way=self.payment_way,
						acc_number=self.parse_to_txt(PartnerAccount.acc_number if PartnerAccount.type_of_account in ['0', '1'] else '', 'str',range=10),
						acc_number_cci=self.parse_to_txt(PartnerAccount.acc_number if PartnerAccount.type_of_account in ['3'] else '', 'str', range=20),
						amount=self.parse_to_txt(amount_to_pay, 'float', range=11, left=False),
						labor_regime='1',
						currency='00' if BankAccount.currency_id.name == 'PEN' else '01',
						concept=self.parse_to_txt('HABERES', 'str', range=20),
						payment_type='02',
					))
		f.close()
		f = open(doc_name, 'rb')
		return self.env['popup.it'].get_file('Scotiabank_Haberes.txt', base64.encodebytes(b''.join(f.readlines())))

	def get_banbif_hr_txt(self, gratification=False):
		MainParameter = self.env['hr.main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
		if not MainParameter or not MainParameter.dir_create_file:
			raise UserError(u'No existe un Directorio de Descarga configurado en Parametros Principales de Nomina para su Compañía')
		doc_name = '%sBanBif_Haberes.txt' % MainParameter.dir_create_file
		f = open(doc_name, 'w+')
		BankAccount = self.journal_id.bank_account_id
		if gratification:
			slip_ids = self.grat_line_ids.filtered(lambda l: l.is_text == True)
		else:
			slip_ids = self.slip_ids.filtered(lambda l: l.is_text == True)
		n=0
		# als=[]
		# for l in self.slip_ids:
		# 	als.append(l.id)

		# for line in self.slip_ids.search([('id','in',als)],order='name'):
		for line in slip_ids:
			PartnerAccount = line.employee_id.wage_bank_account_id
			amount_to_pay = self.get_amount_to_pay(line, gratification)
			if amount_to_pay>0:
				n=n+1
				ap=str(round(amount_to_pay,2))
				apf=''
				if '.' in ap:
					apa=ap.split('.')
					if len(apa[1])<2:
						apf=apa[0]+'.'+apa[1].ljust(2,'0')
					else:
						apf=ap
				else:
					apf=ap+'.00'
				apf=apf.replace('.','').rjust(14,' ')
				f.write('{numcor}{p_doc_type}{p_doc_num}{apepat}{apemat}{names}{street}{phone}{platype}{codbank}{account_number}{currency_type}{amount}{motdep}'.format(
					numcor=str(n).rjust(7,' '),
					p_doc_type=line.employee_id.type_document_id.banbif_code,
					p_doc_num=self.parse_to_txt(line.employee_id.identification_id, 'str', range=11,left=True),
					apepat=self.parse_to_txt(line.employee_id.last_name, 'str', range=20,left=True),
					apemat=self.parse_to_txt(line.employee_id.m_last_name, 'str', range=20,left=True),
					names=self.parse_to_txt(line.employee_id.names, 'str', range=44,left=True),
					street=self.parse_to_txt(line.employee_id.address_home_id.street if line.employee_id.address_home_id.street else 'SIN DIRECCION', 'str', range=60,left=True),
					phone=self.parse_to_txt(line.employee_id.address_home_id.mobile if line.employee_id.address_home_id.mobile else 'SINTELEFON', 'str', range=10,left=True),
					platype='H',
					codbank=PartnerAccount.bank_id.bic or '038',
					account_number=PartnerAccount.acc_number.rjust(20,' '),
					currency_type='1',
					#amount=self.parse_to_txt(amount_to_pay, 'float', range=14, left=False),
					amount=apf,
					motdep=self.subtypebanbif,
				)+ '\r\n')
		f.close()
		f = open(doc_name, 'rb')
		return self.env['popup.it'].get_file('BanBif_Haberes.txt', base64.encodebytes(b''.join(f.readlines())))


	# CTS
	def get_cts_txt(self):
		if not self.journal_id.bank_account_id:
			raise UserError('El diario seleccionado no tiene una cuenta bancaria definida')
		if self.format_bank == 'bbva':
			self.verify_bbva_cts_fields()
			return self.get_bbva_cts_txt()
		elif self.format_bank == 'bcp':
			self.verify_bcp_cts_fields()
			return self.get_bcp_cts_txt()
		elif self.format_bank == 'interbank':
			self.verify_interbank_cts_fields()
			return self.get_interbank_cts_txt()
		elif self.format_bank == 'scotiabank':
			self.verify_scotiabank_cts_fields()
			return self.get_scotiabank_cts_txt()
		elif self.format_bank == 'banbif':
			#self.verify_banbif_cts_fields()
			return self.get_banbif_cts_txt()
		else:
			raise UserError('El diario no tiene un banco con formato definido')

	def verify_bbva_cts_fields(self):
		log = ''
		BankAccount = self.journal_id.bank_account_id
		log += self.check_account_type(BankAccount, 'bbva')
		if BankAccount.type_of_account == '3':
			log += 'No se puede utilizar la cuenta %s de tipo interbancaria como cuenta de cargo\n' % BankAccount.acc_number
		if not self.process_type:
			log += 'Necesita especificar un tipo de proceso\n'
		Lines = self.get_cts_lines()
		for line in Lines:
			if not line.employee_id.type_document_id.bbva_code:
				log += 'El tipo de documento del partner %s no tiene su codigo BBVA\n' % line.employee_id.name
			if not line.employee_id.identification_id:
				log += 'El partner %s no tiene un numero de documento asignado\n' % line.employee_id.name
			PartnerAccount = line.employee_id.cts_bank_account_id
			log += self.check_account_type(PartnerAccount, 'bbva')
		if log:
			raise UserError('Se han detectado los siguientes errores\n' + log)

	def verify_bcp_cts_fields(self):
		log = ''
		BankAccount = self.journal_id.bank_account_id
		log += self.check_account_type(BankAccount, 'bcp')
		if BankAccount.type_of_account == '3':
			log += 'No se puede utilizar la cuenta %s de tipo interbancaria como cuenta de cargo\n' % BankAccount.acc_number
		if not self.env.company.vat:
			log += 'La compañia %s no tiene un numero de ruc configurado\n' % self.env.company.name
		Lines = self.get_cts_lines()
		for line in Lines:
			if not line.employee_id.type_document_id.bcp_code:
				log += 'El tipo de documento del partner %s no tiene su codigo BCP\n' % line.employee_id.name
			if not line.employee_id.identification_id:
				log += 'El partner %s no tiene un numero de documento asignado\n' % line.employee_id.name
			PartnerAccount = line.employee_id.cts_bank_account_id
			log += self.check_account_type(PartnerAccount, 'bcp')
		if log:
			raise UserError('Se han detectado los siguientes errores\n' + log)

	def verify_interbank_cts_fields(self):
		log = ''
		BankAccount = self.journal_id.bank_account_id
		log += self.check_account_type(BankAccount, 'interbank')
		if BankAccount.type_of_account == '3':
			log += 'No se puede utilizar la cuenta %s de tipo interbancaria como cuenta de cargo\n' % BankAccount.acc_number
		if not self.company_code:
			log += 'El codigo de compañia es un campo obligatorio\n'
		if not self.service_code:
			log += 'El codigo de servicio es un campo obligatorio\n'
		if not self.process_type_interbank:
			log += 'El tipo de proceso es un campo obligatorio\n'
		if not self.person_type:
			log += 'El tipo de persona es un campo obligatorio\n'
		Lines = self.get_cts_lines()
		for line in Lines:
			if not line.employee_id.type_document_id.interbank_code:
				log += 'El tipo de documento del partner %s no tiene su codigo Interbank\n' % line.employee_id.name
			if not line.employee_id.identification_id:
				log += 'El partner %s no tiene un numero de documento asignado\n' % line.employee_id.name
			PartnerAccount = line.employee_id.cts_bank_account_id
			log += self.check_account_type(PartnerAccount, 'interbank')
		if log:
			raise UserError('Se han detectado los siguientes errores\n' + log)

	def verify_scotiabank_cts_fields(self):
		log = ''
		BankAccount = self.journal_id.bank_account_id
		log += self.check_account_type(BankAccount, 'scotiabank')
		if not self.charge_type:
			log += 'El Tipo de Abono es un campo obligatorio\n'
		Lines = self.get_cts_lines()
		for line in Lines:
			PartnerAccount = line.employee_id.cts_bank_account_id
			log += self.check_account_type(PartnerAccount, 'scotiabank')

	def get_amounts_total_cts(self, Lines):
		if self.cts_dollars:
			amounts = Lines.mapped('cts_dollars')
		else:
			amounts = Lines.mapped('cts_soles')
		return sum(amounts)

	def get_cts_lines(self):
		if self.cts_dollars:
			Lines = self.cts_line_ids.filtered(lambda l: l.employee_id.cts_bank_account_id.currency_id.name == 'USD' and l.is_text == True)
		else:
			Lines = self.cts_line_ids.filtered(lambda l: l.employee_id.cts_bank_account_id.currency_id.name == 'PEN' and l.is_text == True)
		return Lines

	def get_bbva_cts_txt(self):
		MainParameter = self.env['hr.main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
		if not MainParameter or not MainParameter.dir_create_file:
			raise UserError(
				u'No existe un Directorio de Descarga configurado en Parametros Principales de Nomina para su Compañía')
		doc_name = '%sBBVA_CTS.txt' % MainParameter.dir_create_file
		f = open(doc_name, 'w+')
		BankAccount = self.journal_id.bank_account_id
		acc_number = BankAccount.acc_number[:8] + BankAccount.branch_name + BankAccount.acc_number[8:]
		Lines = self.get_cts_lines()
		amounts_total = self.get_amounts_total_cts(Lines)
		f.write('{code}{account}{currency}{total}{process}{date}{hour}{reference}{lines}{valid}'.format(
			code=610 if self.cts_dollars else 600,
			account=acc_number,
			currency='USD' if self.cts_dollars else 'PEN',
			total=self.parse_to_txt(amounts_total, 'float', range=15, left=False),
			process='F',
			date=self.parse_to_txt(self.payment_date, 'date') if self.process_type == 'F' else ' ' * 8,
			hour='D',
			reference=self.parse_to_txt(self.glosa, 'str', range=25) if self.glosa else ' ' * 25,
			# lines=self.parse_to_txt(len(Lines), 'int', range=6),
			lines=str(len(Lines)).zfill(6),
			valid=self.owner_validation,
		) + ' ' * 68 + '\r\n')
		for line in Lines:
			PartnerAccount = line.employee_id.cts_bank_account_id
			if self.alert_indicator == 'E':
				alert_val = line.employee_id.work_email or ''
			elif self.alert_indicator == 'C':
				alert_val = line.employee_id.work_phone or ''
			else:
				alert_val = ''
			if line.cts_dollars>0 or  line.cts_soles>0:
				f.write('002{p_doc_type}{p_doc_num}{charge_type}{payment_doc}{beneficiary_name}{amount}\
	{reference}{alert_indicator}{alert_val}{whites}{last_6_rem}{amount_currency}{filler}\r\n'.format(
					p_doc_type=line.employee_id.type_document_id.bbva_code,
					p_doc_num=self.parse_to_txt(line.employee_id.identification_id, 'str', range=12),
					charge_type='I' if PartnerAccount.type_of_account == '3' else 'P',
					payment_doc=self.parse_to_txt(PartnerAccount.acc_number, 'str', range=20),
					beneficiary_name=self.parse_to_txt(line.employee_id.name, 'str', range=40),
					amount=self.parse_to_txt(line.cts_dollars if self.cts_dollars else line.cts_soles, 'float', range=15, left=False),
					reference=self.parse_to_txt(line.cts_id.name, 'str', range=40),
					alert_indicator=self.alert_indicator if self.alert_indicator else ' ',
					alert_val=self.parse_to_txt(alert_val, 'str', range=50),
					whites=' ' * 53,
					last_6_rem=' ' * 15,
					amount_currency='USD' if self.cts_dollars else 'PEN',
					filler=' ' * 18,
				))
		f.close()
		f = open(doc_name, 'rb')
		return self.env['popup.it'].get_file('BBVA_CTS.txt', base64.encodebytes(b''.join(f.readlines())))

	def get_bcp_cts_txt(self):
		MainParameter = self.env['hr.main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
		if not MainParameter or not MainParameter.dir_create_file:
			raise UserError(
				u'No existe un Directorio de Descarga configurado en Parametros Principales de Nomina para su Compañía')
		doc_name = '%sBCP_CTS.txt' % MainParameter.dir_create_file
		f = open(doc_name, 'w+')
		BankAccount = self.journal_id.bank_account_id
		# acc_numbers = [int(self.get_acc(i.partner_id, self.journal_id).acc_number) for i in self.invoice_ids]
		# acc_numbers.append(int(BankAccount.acc_number))
		# check_sum = sum(acc_numbers)
		Lines = self.get_cts_lines()
		amounts_total = self.get_amounts_total_cts(Lines)

		f.write(
			'1{lines}{date}{charge_type}{currency}{account}{company_doc}{company_ruc}{total}{reference}{check_sum}\r\n'.format(
				lines=self.parse_to_txt(len(Lines), 'int', range=6, left=False),
				date=self.parse_to_txt(self.payment_date, 'date'),
				charge_type='C',
				currency='1001' if self.cts_dollars else '0001',
				account=self.parse_to_txt(BankAccount.acc_number, 'str', range=20),
				company_doc=6,
				company_ruc=self.parse_to_txt(self.env.company.vat, 'str', range=12),
				total=self.parse_to_txt(amounts_total, 'float', range=17, left=False, decimal_point=True),
				reference=self.parse_to_txt(self.glosa, 'str', range=40),
				check_sum=' ' * 15,
			))
		for line in Lines:
			PartnerAccount = line.employee_id.cts_bank_account_id
			if line.cts_dollars>0 or  line.cts_soles>0:
				f.write('2{payment_doc}{p_doc_type}{p_doc_num}   {beneficiary_name}\
	{beneficiary_ref}{company_ref}{currency}{amount}\r\n'.format(
					payment_doc=self.parse_to_txt(PartnerAccount.acc_number, 'str', range=20),
					p_doc_type=line.employee_id.type_document_id.bcp_code,
					p_doc_num=self.parse_to_txt(line.employee_id.identification_id, 'str', range=12),
					beneficiary_name=self.parse_to_txt(line.employee_id.name, 'str', range=75),
					beneficiary_ref=self.parse_to_txt(line.cts_id.name, 'str', range=40),
					company_ref=self.parse_to_txt(self.env.company.name, 'str', range=20),
					currency='1001' if self.cts_dollars else '0001',
					amount=self.parse_to_txt(line.cts_dollars if self.cts_dollars else line.cts_soles,'float', range=17, left=False, decimal_point=True),
				))
		f.close()
		f = open(doc_name, 'rb')
		return self.env['popup.it'].get_file('BCP_CTS.txt', base64.encodebytes(b''.join(f.readlines())))

	def get_interbank_cts_txt(self):
		MainParameter = self.env['hr.main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
		if not MainParameter or not MainParameter.dir_create_file:
			raise UserError(
				u'No existe un Directorio de Descarga configurado en Parametros Principales de Nomina para su Compañía')
		doc_name = '%sInterbank_CTS.txt' % MainParameter.dir_create_file
		f = open(doc_name, 'w+')
		BankAccount = self.journal_id.bank_account_id
		Lines = self.get_cts_lines()
		amounts_total = self.get_amounts_total_cts(Lines)
		after_date = fields.Date.today() if self.process_type_interbank == '0' else self.payment_date
		f.write('0104{company}{service}{account}{type_account}{currency}{reference}{date}{process_type}\
{after_date}{lines}{soles_total}{usd_total}MC001\r\n'.format(
			company=self.parse_to_txt(self.company_code, 'str', range=4),
			service=self.parse_to_txt(self.service_code, 'str', range=2),
			account=self.parse_to_txt(BankAccount.acc_number, 'str', range=13),
			type_account='001' if BankAccount.type_of_account == '0' else '002',
			currency='10' if self.cts_dollars else '01',
			reference=self.parse_to_txt(self.glosa, 'str', range=12),
			date=self.parse_to_txt(fields.Datetime.now(), 'datetime'),
			process_type=self.process_type_interbank,
			after_date=self.parse_to_txt(after_date, 'date'),
			lines=self.parse_to_txt(len(Lines), 'int', range=6),
			soles_total=self.parse_to_txt(amounts_total, 'float', range=15) if not self.cts_dollars else '0' * 15,
			usd_total=self.parse_to_txt(amounts_total, 'float', range=15) if self.cts_dollars else '0' * 15,
		))
		for line in Lines:
			PartnerAccount = line.employee_id.cts_bank_account_id
			ACCOUNT_TYPE = {'0': '001', '1': '002', '3': ' ' * 3}
			if self.person_type == 'P':
				benef_name = self.parse_to_txt(line.employee_id.names or '', 'str', range=20) + \
							 self.parse_to_txt(line.employee_id.last_name or '', 'str', range=20) + \
							 self.parse_to_txt(line.employee_id.m_last_name or '', 'str', range=20)
			else:
				benef_name = self.parse_to_txt(line.employee_id.name, 'str', range=60)
			if line.cts_dollars>0 or  line.cts_soles>0:
				f.write('02{benef_code}{doc_type}{doc_number}{date_to}{charge_currency}{amount} {charge_type}{account_type}\
	{account_currency}{account_office}{acc_number}{person_type}{p_doc_type}{p_doc_num}{benef_name}{currency_cts}{amount_cts}\
	{filler}{cell_phone}{email}\r\n'.format(
					benef_code=self.parse_to_txt(line.employee_id.identification_id, 'str', range=20),
					doc_type=' ',
					doc_number=' ' * 20,
					date_to=' ' * 8,
					charge_currency='10' if self.cts_dollars else '01',
					amount=self.parse_to_txt(line.cts_dollars if self.cts_dollars else line.cts_soles, 'float', range=15),
					charge_type='99' if PartnerAccount.type_of_account == '3' else '09',
					account_type=ACCOUNT_TYPE.get(PartnerAccount.type_of_account, ' ' * 3),
					account_currency=' ' * 2 if PartnerAccount.type_of_account == '3' else ('10' if self.cts_dollars else '01'),
					account_office=' ' * 3 if PartnerAccount.type_of_account == '3' else PartnerAccount.acc_number[:3],
					acc_number=PartnerAccount.acc_number if PartnerAccount.type_of_account == '3' else self.parse_to_txt(PartnerAccount.acc_number[:3], 'str', range=20),
					person_type=self.person_type if self.person_type else ' ',
					p_doc_type=line.employee_id.type_document_id.interbank_code,
					p_doc_num=self.parse_to_txt(line.employee_id.identification_id, 'str', range=15),
					benef_name=benef_name,
					currency_cts='10' if self.cts_dollars else '01',
					amount_cts=self.parse_to_txt(line.cts_dollars if self.cts_dollars else line.cts_soles, 'float', range=15),
					filler=' ' * 6,
					cell_phone=self.parse_to_txt(line.employee_id.work_phone or '', 'str', range=40),
					email=self.parse_to_txt(line.employee_id.work_email or '', 'str', range=140),
				))
		f.close()
		f = open(doc_name, 'rb')
		return self.env['popup.it'].get_file('Interbank_CTS.txt', base64.encodebytes(b''.join(f.readlines())))

	def get_scotiabank_cts_txt(self):
		MainParameter = self.env['hr.main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
		if not MainParameter or not MainParameter.dir_create_file:
			raise UserError(
				u'No existe un Directorio de Descarga configurado en Parametros Principales de Nomina para su Compañía')
		doc_name = '%sScotiabank_CTS.txt' % MainParameter.dir_create_file
		f = open(doc_name, 'w+')
		BankAccount = self.journal_id.bank_account_id
		Lines = self.get_cts_lines()
		amounts_total = self.get_amounts_total_cts(Lines)
		# f.write('0{charge_type}{company_code}{currency}{total}\r\n'.format(
		#	charge_type=self.charge_type,
		#	company_code=' ' * 10,
		#	currency='01' if self.cts_dollars else '92',
		#	total=self.parse_to_txt(amounts_total, 'float', range=15),
		# ))

		for line in Lines:
			PartnerAccount = line.employee_id.cts_bank_account_id
			if self.cts_dollars:
				rem_amount = self.env['report.base'].custom_round(line.wage / line.exchange_type, 2)
			else:
				rem_amount = line.wage
			if line.cts_dollars>0 or  line.cts_soles>0:
				f.write(
					'{type_document}{number_document}{emp_name}{payment_method}{cts_acc}{cci_acc}{rem_amount}{cts_currency}{concept}{type_payment}\r\n'.format(
						type_document=line.employee_id.type_document_id.sunat_code,
						number_document=line.employee_id.identification_id.ljust(12),
						emp_name1=line.employee_id.name.ljust(60),
						emp_name=self.delete_special_chars(line.employee_id.name.ljust(60)),
						cts_currency='01' if self.cts_dollars else '00',
						payment_method='1',  # Abono en Cts CTS (CCI = 2)
						cts_acc=line.employee_id.cts_bank_account_id.acc_number[0:10],
						# cts_acc=self.parse_to_txt(
						#	PartnerAccount.acc_number if PartnerAccount.type_of_account in ['0', '1'] else '', 'str', range=10),
						amount=self.parse_to_txt(line.cts_dollars if self.cts_dollars else line.cts_soles, 'float', range=15),
						cci_acc=self.parse_to_txt(PartnerAccount.acc_number if PartnerAccount.type_of_account == '3' else '', 'str', range=20),
						rem_amount='{0:.2f}'.format(line.cts_soles).replace('.', '').zfill(11),
						type_payment='05',  # CTS
						concept=self.cts_id.name[0:20],
					))
		f.close()
		f = open(doc_name, 'rb')
		return self.env['popup.it'].get_file('Scotiabank_CTS.txt', base64.encodebytes(b''.join(f.readlines())))

	def get_banbif_cts_txt(self):
		MainParameter = self.env['hr.main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
		if not MainParameter or not MainParameter.dir_create_file:
			raise UserError(
				u'No existe un Directorio de Descarga configurado en Parametros Principales de Nomina para su Compañía')
		doc_name = '%sBanBif_CTS.txt' % MainParameter.dir_create_file
		f = open(doc_name, 'w+')
		BankAccount = self.journal_id.bank_account_id
		n=0
		Lines = self.get_cts_lines()
		for line in Lines:
			PartnerAccount = line.employee_id.cts_bank_account_id
			amount_to_pay = line.cts_dollars if self.cts_dollars else line.cts_soles
			n=n+1
			ap=str(round(amount_to_pay,2))
			apf=''
			if '.' in ap:
				apa=ap.split('.')
				if len(apa[1])<2:
					apf=apa[0]+'.'+apa[1].ljust(2,'0')
				else:
					apf=ap
			else:
				apf=ap+'.00'
			apf=apf.replace('.','').rjust(14,' ')
			print(111,PartnerAccount.acc_number.strip().rjust(20,' '),)
			f.write('{numcor}{p_doc_type}{p_doc_num}{apepat}{apemat}{names}{street}{phone}{platype}{codbank}{account_number}{currency_type}{amount}{motdep}'.format(
				numcor=str(n).rjust(7,' '),
				p_doc_type=line.employee_id.type_document_id.banbif_code,
				p_doc_num=self.parse_to_txt(line.employee_id.identification_id, 'str', range=11,left=True),
				apepat=self.parse_to_txt(line.employee_id.last_name, 'str', range=20,left=True),
				apemat=self.parse_to_txt(line.employee_id.m_last_name, 'str', range=20,left=True),
				names=self.parse_to_txt(line.employee_id.names, 'str', range=44,left=True),
				street=self.parse_to_txt(line.employee_id.address_home_id.street if line.employee_id.address_home_id.street else 'SIN DIRECCION', 'str', range=60,left=True),
				phone=self.parse_to_txt(line.employee_id.address_home_id.mobile if line.employee_id.address_home_id.mobile else 'SINTELEFON', 'str', range=10,left=True),
				# p_doc_num=self.parse_to_txt(line.employee_id.identification_id, 'str', range=11,left=True),
				# apepat=self.parse_to_txt(line.employee_id.last_name, 'str', range=20,left=True),
				# apemat=self.parse_to_txt(line.employee_id.m_last_name, 'str', range=20,left=True),
				# names=self.parse_to_txt(line.employee_id.names, 'str', range=44,left=True),
				# street=self.parse_to_txt(line.employee_id.address_home_id.street if line.employee_id.address_home_id.street else ' ', 'str', range=60,left=True),
				# phone=self.parse_to_txt(line.employee_id.address_home_id.mobile if line.employee_id.address_home_id.mobile else ' ', 'str', range=10,left=True),
				platype='C',
				#codbank=PartnerAccount.bank_id.bic or '038',
				codbank=PartnerAccount.bank_id.code_bank,
				account_number=PartnerAccount.acc_number.strip().rjust(20,' '),
				currency_type='2' if self.cts_dollars else '1',
				#amount=self.parse_to_txt(amount_to_pay, 'float', range=14, left=False),
				amount=apf,
				#amount=apf,
				motdep='0'
			)+ '\r\n')

		f.close()
		f = open(doc_name, 'rb')
		return self.env['popup.it'].get_file('BanBif_CTS.txt', base64.encodebytes(b''.join(f.readlines())))


	# UTILIDADES
	def get_utilities_txt(self):
		if not self.journal_id.bank_account_id:
			raise UserError('El diario seleccionado no tiene una cuenta bancaria definida')
		if self.format_bank == 'bbva':
			self.verify_bbva_hr_fields()
			return self.get_bbva_hr_utility_txt()
		elif self.format_bank == 'bcp':
			self.verify_bcp_hr_fields()
			return self.get_bcp_hr_utility_txt()
		elif self.format_bank == 'interbank':
			self.verify_interbank_hr_fields()
			return self.get_interbank_hr_utility_txt()
		elif self.format_bank == 'scotiabank':
			self.verify_scotiabank_hr_fields()
			return self.get_scotiabank_hr_utility_txt_2()
		elif self.format_bank == 'banbif':
			#self.verify_scotiabank_hr_fields()
			return self.get_banbif_hr_utility_txt()
		else:
			raise UserError('El diario no tiene un banco con formato definido')

	def get_amounts_total_hr_utility(self):
		amounts = []
		HrMainParameter = self.env['hr.main.parameter'].search([('company_id', '=', self.company_id.id)])
		rule = self.env['hr.salary.rule'].search([('code','=',HrMainParameter.hr_input_for_results.code)], limit=1)
		for slip in self.slip_ids:
			Line = slip.line_ids.filtered(lambda l: l.salary_rule_id.id == rule.id)
			if len(Line) != 0:
				amounts.append(self.env['report.base'].custom_round(Line.total, 2))
		return sum(amounts)

	def get_amount_to_pay_utility(self, line):
		HrMainParameter = self.env['hr.main.parameter'].search([('company_id', '=', self.company_id.id)])
		rule = self.env['hr.salary.rule'].search([('code','=',HrMainParameter.hr_input_for_results.code)], limit=1)
		Line = line.line_ids.filtered(lambda l: l.salary_rule_id.id == rule.id)
		amount = 0
		if len(Line) != 0:
			amount = Line[0].total
		return amount

	def get_bbva_hr_utility_txt(self):
		MainParameter = self.env['hr.main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
		if not MainParameter or not MainParameter.dir_create_file:
			raise UserError(
				u'No existe un Directorio de Descarga configurado en Parametros Principales de Nomina para su Compañía')
		doc_name = '%sBBVA_Utilidades.txt' % MainParameter.dir_create_file
		f = open(doc_name, 'w+')
		BankAccount = self.journal_id.bank_account_id
		acc_number = BankAccount.acc_number[:8] + BankAccount.branch_name + BankAccount.acc_number[8:]
		amounts_total = self.get_amounts_total_hr_utility()
		f.write('700{account}{currency}{total}{process}{date}{hour}{reference}{lines}{valid}{cero}'.format(
			account=acc_number,
			currency=BankAccount.currency_id.name,
			total=self.parse_to_txt(amounts_total, 'float', range=15, left=False),
			process=self.process_type,
			date=self.parse_to_txt(self.payment_date, 'date') if self.process_type == 'F' else ' ' * 8,
			hour=self.process_hour if self.process_type == 'H' else ' ',
			reference=self.parse_to_txt(self.glosa, 'str', range=25) if self.glosa else ' ' * 25,
			lines=self.parse_to_txt(len(self.slip_ids), 'int', range=6, left=False),
			valid=self.owner_validation,
			cero='0' * 18,
		) + ' ' * 50 + '\r\n')
		for line in self.slip_ids:
			PartnerAccount = line.employee_id.wage_bank_account_id
			if self.alert_indicator == 'E':
				alert_val = line.employee_id.work_email or ''
			elif self.alert_indicator == 'C':
				alert_val = line.employee_id.work_phone or ''
			else:
				alert_val = ''
			amount_to_pay = self.get_amount_to_pay_utility(line)
			if amount_to_pay != 0:
				f.write('002{p_doc_type}{p_doc_num}{charge_type}{payment_doc}{beneficiary_name}{amount}\
{reference}{alert_indicator}{alert_val}'.format(
				p_doc_type=line.employee_id.type_document_id.bbva_code,
				p_doc_num=self.parse_to_txt(line.employee_id.identification_id, 'str', range=12),
				charge_type='I' if PartnerAccount.type_of_account == '3' else 'P',
				payment_doc=self.parse_to_txt(PartnerAccount.acc_number, 'str', range=20),
				beneficiary_name=self.parse_to_txt(line.employee_id.name, 'str', range=40),
				amount=self.parse_to_txt(amount_to_pay, 'float', range=15, left=False),
				reference=self.parse_to_txt(line.number, 'str', range=40),
				alert_indicator=self.alert_indicator if self.alert_indicator else ' ',
				alert_val=self.parse_to_txt(alert_val, 'str', range=50),
			) + ' ' * 50 + '\r\n')
		f.close()
		f = open(doc_name, 'rb')
		return self.env['popup.it'].get_file('BBVA_Utilidades.txt', base64.encodebytes(b''.join(f.readlines())))

	def get_bcp_hr_utility_txt(self):
		MainParameter = self.env['hr.main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
		if not MainParameter or not MainParameter.dir_create_file:
			raise UserError(
				u'No existe un Directorio de Descarga configurado en Parametros Principales de Nomina para su Compañía')
		doc_name = '%sBCP_Utilidades.txt' % MainParameter.dir_create_file
		f = open(doc_name, 'w+')
		BankAccount = self.journal_id.bank_account_id
		ACCOUNT_TYPE = {'0': 'C', '1': 'A', '3': 'B'}

		acc_numbers = []
		for i in self.slip_ids:
			PartnerAccount = i.employee_id.wage_bank_account_id
			if PartnerAccount.type_of_account == '3':
				acc_numbers.append(int(PartnerAccount.acc_number[10:]))
			else:
				acc_numbers.append(int(PartnerAccount.acc_number[3:]))
		acc_numbers.append(int(BankAccount.acc_number[3:]))
		check_sum = sum(acc_numbers)
		amounts_total = self.get_amounts_total_hr_utility()

		f.write('1{lines}{date}{subtype}{charge_type}{currency}{account}{total}{reference}{check_sum}\r\n'.format(
			lines=self.parse_to_txt(len(self.slip_ids), 'int', range=6, left=False),
			date=self.parse_to_txt(self.payment_date, 'date'),
			subtype=self.subtype,
			charge_type='C',
			currency='0001' if BankAccount.currency_id.name == 'PEN' else '1001',
			account=self.parse_to_txt(BankAccount.acc_number, 'str', range=20),
			total=self.parse_to_txt(amounts_total, 'float', range=17, left=False, decimal_point=True),
			reference=self.parse_to_txt(self.glosa, 'str', range=40),
			check_sum=self.parse_to_txt(str(check_sum), 'str', range=15),
		))
		for line in self.slip_ids:
			PartnerAccount = line.employee_id.wage_bank_account_id
			amount_to_pay = self.get_amount_to_pay_utility(line)
			if amount_to_pay != 0:
				f.write('2{account_type}{payment_doc}{p_doc_type}{p_doc_num}   {beneficiary_name}\
{beneficiary_ref}{company_ref}{currency}{amount}{flag}\r\n'.format(
				account_type=ACCOUNT_TYPE.get(PartnerAccount.type_of_account, ' '),
				payment_doc=self.parse_to_txt(PartnerAccount.acc_number, 'str', range=20),
				p_doc_type=line.employee_id.type_document_id.bcp_code,
				p_doc_num=self.parse_to_txt(line.employee_id.identification_id, 'str', range=12),
				beneficiary_name=self.parse_to_txt(line.employee_id.name, 'str', range=75),
				beneficiary_ref=self.parse_to_txt(line.number, 'str', range=40),
				company_ref=self.parse_to_txt(self.env.company.name, 'str', range=20),
				currency='0001' if BankAccount.currency_id.name == 'PEN' else '1001',
				amount=self.parse_to_txt(amount_to_pay, 'float', range=17, left=False, decimal_point=True),
				flag='S' if self.idc_flag else 'N',
			))
		f.close()
		f = open(doc_name, 'rb')
		return self.env['popup.it'].get_file('BCP_Utilidades.txt', base64.encodebytes(b''.join(f.readlines())))

	def get_interbank_hr_utility_txt(self):
		MainParameter = self.env['hr.main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
		if not MainParameter or not MainParameter.dir_create_file:
			raise UserError(
				u'No existe un Directorio de Descarga configurado en Parametros Principales de Nomina para su Compañía')
		doc_name = '%sInterbank_Utilidades.txt' % MainParameter.dir_create_file
		f = open(doc_name, 'w+')
		BankAccount = self.journal_id.bank_account_id
		after_date = fields.Date.today() if self.process_type_interbank == '0' else self.payment_date
		amounts_total = self.get_amounts_total_hr_utility()
		f.write('0104{company}{service}{account}{type_account}{currency}{reference}{date}{process_type}\
{after_date}{lines}{soles_total}{usd_total}MC001\r\n'.format(
			company=self.parse_to_txt(self.company_code, 'str', range=4),
			service=self.parse_to_txt(self.service_code, 'str', range=2),
			account=self.parse_to_txt(BankAccount.acc_number, 'str', range=13),
			type_account='001' if BankAccount.type_of_account == '0' else '002',
			currency='01' if BankAccount.currency_id.name == 'PEN' else '10',
			reference=self.parse_to_txt(self.glosa, 'str', range=12),
			date=self.parse_to_txt(fields.Datetime.now(), 'datetime'),
			process_type=self.process_type_interbank,
			after_date=self.parse_to_txt(after_date, 'date'),
			lines=self.parse_to_txt(len(self.slip_ids), 'int', range=6),
			soles_total=self.parse_to_txt(amounts_total, 'float', range=15) if BankAccount.currency_id.name == 'PEN' else '0' * 15,
			usd_total=self.parse_to_txt(amounts_total, 'float',	range=15) if BankAccount.currency_id.name == 'USD' else '0' * 15,
		))
		for line in self.slip_ids:
			PartnerAccount = line.employee_id.wage_bank_account_id
			ACCOUNT_TYPE = {'0': '001', '1': '002', '3': ' ' * 3}
			if self.person_type == 'P':
				benef_name = self.parse_to_txt(line.employee_id.names or '', 'str', range=20) + \
							 self.parse_to_txt(line.employee_id.last_name or '', 'str', range=20) + \
							 self.parse_to_txt(line.employee_id.m_last_name or '', 'str', range=20)
			else:
				benef_name = self.parse_to_txt(line.employee_id.name, 'str', range=60)
			amount_to_pay = self.get_amount_to_pay_utility(line)
			if amount_to_pay != 0:
				f.write('02{benef_code}{doc_type}{doc_number}{date_to}{charge_currency}{amount} {charge_type}{account_type}\
{account_currency}{account_office}{acc_number}{person_type}{p_doc_type}{p_doc_num}{benef_name}{currency_cts}{amount_cts}\
{filler}{cell_phone}{email}\r\n'.format(
				benef_code=self.parse_to_txt(line.employee_id.identification_id, 'str', range=20),
				doc_type=' ',
				doc_number=' ' * 20,
				date_to=' ' * 8,
				charge_currency='01' if BankAccount.currency_id.name == 'PEN' else '10',
				amount=self.parse_to_txt(amount_to_pay, 'float', range=15),
				charge_type='99' if PartnerAccount.type_of_account == '3' else '09',
				account_type=ACCOUNT_TYPE.get(PartnerAccount.type_of_account, ' ' * 3),
				account_currency=' ' * 2 if PartnerAccount.type_of_account == '3' else ('01' if BankAccount.currency_id.name == 'PEN' else '10'),
				account_office=' ' * 3 if PartnerAccount.type_of_account == '3' else PartnerAccount.acc_number[:3],
				acc_number=PartnerAccount.acc_number if PartnerAccount.type_of_account == '3' else self.parse_to_txt(PartnerAccount.acc_number[:3], 'str', range=20),
				person_type=self.person_type if self.person_type else ' ',
				p_doc_type=line.employee_id.type_document_id.interbank_code,
				p_doc_num=self.parse_to_txt(line.employee_id.identification_id, 'str', range=15),
				benef_name=benef_name,
				currency_cts=' ' * 2,
				amount_cts=' ' * 15,
				filler=' ' * 6,
				cell_phone=self.parse_to_txt(line.employee_id.work_phone or '', 'str', range=40),
				email=self.parse_to_txt(line.employee_id.work_email or '', 'str', range=140),
			))
		f.close()
		f = open(doc_name, 'rb')
		return self.env['popup.it'].get_file('Interbank_Utilidades.txt', base64.encodebytes(b''.join(f.readlines())))

	def get_scotiabank_hr_utility_txt_2(self):
		MainParameter = self.env['hr.main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
		if not MainParameter or not MainParameter.dir_create_file:
			raise UserError(
				u'No existe un Directorio de Descarga configurado en Parametros Principales de Nomina para su Compañía')
		doc_name = '%sScotiabank_Utilidades.txt' % MainParameter.dir_create_file
		f = open(doc_name, 'w+')
		BankAccount = self.journal_id.bank_account_id
		DOC_TYPE = {'1': '1', '4': '2', '7': '3'}
		for line in self.slip_ids:
			PartnerAccount = line.employee_id.wage_bank_account_id
			amount_to_pay = self.get_amount_to_pay_utility(line)
			if amount_to_pay != 0:
				f.write(
				'{doc_type}{doc_number}{employee_name}{payment_way}{acc_number}{acc_number_cci}{amount}{labor_regime}{currency}{concept}{payment_type}\r\n'.format(
					doc_type=DOC_TYPE.get(line.employee_id.type_document_id.sunat_code, ' '),
					doc_number=self.parse_to_txt(line.employee_id.identification_id.strip(), 'str', range=12),
					employee_name=self.parse_to_txt(line.employee_id.name, 'str', range=60),
					payment_way=self.payment_way,
					acc_number=self.parse_to_txt(PartnerAccount.acc_number if PartnerAccount.type_of_account in ['0', '1'] else '', 'str', range=10),
					acc_number_cci=self.parse_to_txt(PartnerAccount.acc_number if PartnerAccount.type_of_account in ['3'] else '', 'str', range=20),
					amount=self.parse_to_txt(amount_to_pay, 'float', range=11, left=False),
					labor_regime='1',
					currency='00' if BankAccount.currency_id.name == 'PEN' else '01',
					concept=self.parse_to_txt('HABERES', 'str', range=20),
					payment_type='02',
				))
		f.close()
		f = open(doc_name, 'rb')
		return self.env['popup.it'].get_file('Scotiabank_Utilidades.txt', base64.encodebytes(b''.join(f.readlines())))

	def get_banbif_hr_utility_txt(self):
		MainParameter = self.env['hr.main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
		if not MainParameter or not MainParameter.dir_create_file:
			raise UserError(
				u'No existe un Directorio de Descarga configurado en Parametros Principales de Nomina para su Compañía')
		doc_name = '%sBanBif_Utilidades.txt' % MainParameter.dir_create_file
		f = open(doc_name, 'w+')
		BankAccount = self.journal_id.bank_account_id
		n=0
		for line in self.slip_ids:
			PartnerAccount = line.employee_id.wage_bank_account_id
			amount_to_pay = self.get_amount_to_pay_utility(line)
			n=n+1
			ap=str(round(amount_to_pay,2))
			apf=''
			if '.' in ap:
				apa=ap.split('.')
				if len(apa[1])<2:
					apf=apa[0]+'.'+apa[1].ljust(2,'0')
				else:
					apf=ap
			else:
				apf=ap+'.00'
			apf=apf.replace('.','').rjust(14,' ')
			f.write('{numcor}{p_doc_type}{p_doc_num}{apepat}{apemat}{names}{street}{phone}{platype}{codbank}{account_number}{currency_type}{amount}{motdep}'.format(
				numcor=str(n).rjust(7,'0'),
				p_doc_type=line.employee_id.type_document_id.banbif_code,
				p_doc_num=self.parse_to_txt(line.employee_id.identification_id, 'str', range=11,left=True),
				apepat=self.parse_to_txt(line.employee_id.last_name, 'str', range=20,left=True),
				apemat=self.parse_to_txt(line.employee_id.m_last_name, 'str', range=20,left=True),
				names=self.parse_to_txt(line.employee_id.names, 'str', range=44,left=True),
				street=self.parse_to_txt(line.employee_id.address_home_id.street if line.employee_id.address_home_id.street else ' ', 'str', range=60,left=True),
				phone=self.parse_to_txt(line.employee_id.address_home_id.mobile if line.employee_id.address_home_id.mobile else ' ', 'str', range=10,left=True),
				platype='H',
				codbank=PartnerAccount.bank_id.code_bank,
				account_number=PartnerAccount.acc_number.rjust(20,'0'),
				currency_type='1',
				#amount=self.parse_to_txt(amount_to_pay, 'float', range=14, left=False),
				amount=apf,
				motdep='4'
			)+ '\r\n')
		f.close()
		f = open(doc_name, 'rb')
		return self.env['popup.it'].get_file('BanBif_Utilidades.txt', base64.encodebytes(b''.join(f.readlines())))
