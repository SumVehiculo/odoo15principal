# -*- coding:utf-8 -*-
import base64
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError
from odoo.osv import osv, expression
import io
import datetime
from dateutil.relativedelta import relativedelta
from xlsxwriter.workbook import Workbook

class hr_quincenales(models.Model):
	_name = 'hr.quincenales'
	_description = 'hr quincenales'
	_rec_name = 'fecha'

	payslip_run_id = fields.Many2one('hr.payslip.run', string='Planilla', required=True, states={'exported': [('readonly', True)]})
	fecha = fields.Date('Fecha de Pago', required=True)
	state = fields.Selection([('draft', 'Borrador'), ('exported', 'Exportado')], default='draft', string='Estado')
	quincenales_lines = fields.One2many('hr.quincenales.lines', 'quincenal_id', 'lineas')
	company_id = fields.Many2one('res.company', string=u'Compañia', default=(lambda self: self.env.company.id), readonly=True)

	# @api.model
	# def create(self, vals):
	# 	if len(self.env['hr.quincenales'].search([('fecha', '=', vals['fecha'])])):
	# 		raise osv.except_osv('Alerta!', 'Ya existe un registro de quincena con la misma fecha ' + vals['fecha'])
	# 	t = super(hr_quincenales, self).create(vals)
	# 	return t

	# def write(self, vals):
	# 	t = super(hr_quincenales, self).write(vals)
	# 	self.refresh()
	# 	if 'fecha' in vals:
	# 		if len(self.env['hr.quincenales'].search([('fecha', '=', vals['fecha'])])) > 1:
	# 			raise osv.except_osv('Alerta!', 'Ya existe un registro de quincena con la misma fecha ' + vals['fecha'])
	# 		for i in self.quincenales_lines:
	# 			i.unlink()
	# 	return t

	def regresar_borrador(self):
		self.state = 'draft'

	def unlink(self):
		for rec in self:
			if rec.state in ('exported'):
				raise UserError("No puedes eliminar una quincena que ya fue Exportado.")
		return super(hr_quincenales, self).unlink()

	def generate(self):
		ReportBase = self.env['report.base']
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		structure_type_id = self.env['hr.payroll.structure.type'].search([('default_schedule_pay', '=', 'monthly')],limit=1).id
		he = self.env['hr.employee'].search([('contract_ids.state', 'in', ('open', 'close')),('contract_ids.structure_type_id', '=', structure_type_id),
											 ('company_id', '=', self.env.company.id)])

		dateini = str(self.fecha.year) + '-' + str(self.fecha.month).rjust(2, '0') + '-01'
		nfecha = datetime.datetime.strptime(dateini, '%Y-%m-%d')
		contracts = he._get_contracts(nfecha, (self.fecha), states=['open', 'close'])
		# print("contracts",contracts)
		to_create = []
		for contrato in contracts:
			af = MainParameter.rmv * 0.1
			membership = contrato.membership_id
			onp = afp_jub = afp_si = afp_mixed_com = afp_fixed_com = 0
			sueldo = contrato.wage + (af if contrato.employee_id.children > 0 else 0)
			if MainParameter.compute_afiliacion:
				if membership.is_afp:
					afp_jub = ReportBase.custom_round(membership.retirement_fund / 100 * sueldo, 2)
					afp_si = ReportBase.custom_round(membership.prima_insurance / 100 * sueldo, 2)
					if contrato.commision_type=='flow':
						afp_fixed_com = ReportBase.custom_round(membership.fixed_commision / 100 * sueldo, 2)
					if contrato.commision_type=='mixed':
						afp_mixed_com = ReportBase.custom_round(membership.mixed_commision / 100 * sueldo, 2)
				else:
					onp = ReportBase.custom_round(membership.retirement_fund / 100 * sueldo, 2)
			quin_desc = 0
			vals = {
				'quincenal_id':self.id,
				'employee_id':contrato.employee_id.id,
				'contract_id':contrato.id,
				'codigo_trabajador':contrato.employee_id.identification_id,
				'nombres':contrato.employee_id.name,
				'fecha_ingreso':contrato.date_start,
				'basico':contrato.wage,
				'asignacion_familiar':af if contrato.employee_id.children > 0 else 0,
				'onp':onp,
				'afp_com':afp_mixed_com + afp_fixed_com,
				'afp_prima':afp_si,
				'afp_jub':afp_jub,
				'quinta_cat':quin_desc}
			to_create.append(vals)

		for v in to_create:
			hql = self.env['hr.quincenales.lines'].search([('employee_id', '=', v['employee_id']), ('quincenal_id', '=', v['quincenal_id'])])
			if len(hql):
				hql[0].write(v)
			else:
				self.env['hr.quincenales.lines'].create(v)

	def import_advances(self):
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		if not MainParameter.quin_advance_id:
			raise UserError('No se ha configurado un tipo de adelanto para Pagos Quincenales en Parametros Generales')
		log = ''
		Lot = self.payslip_run_id
		to_create = []
		for line in self.quincenales_lines:
			sql = """
					select sum(ha.amount) as amount,
					ha.employee_id,
					hat.input_id
					from hr_advance ha
					inner join hr_advance_type hat on hat.id = ha.advance_type_id
					where ha.discount_date >= '{0}' and
						  ha.discount_date <= '{1}' and
						  ha.employee_id = {2} and
						  ha.state = 'not payed' and
						  hat.id = {3}
					group by ha.employee_id, hat.input_id
					""".format(Lot.date_start, Lot.date_end, line.employee_id.id, MainParameter.quin_advance_id.id)
			self._cr.execute(sql)
			res_data = self._cr.dictfetchall()
			# print("res_data",res_data)

			if res_data:
				hql = self.env['hr.quincenales.lines'].search([('quincenal_id', '=', self.id),('employee_id', '=', line.employee_id.id)], limit=1)
				# if len(hql):
				vals = {
						'quincenal_line_id':hql.id,
						'name_input_id': res_data[0]['input_id'],
						'amount': res_data[0]['amount'],
						'type': 'out',
					}
				to_create.append(vals)
				# print("vals if",vals)

				for v in to_create:
					hqcl = self.env['hr.quincenales.conceptos.lines'].search([('quincenal_line_id', '=', v['quincenal_line_id']),('name_input_id', '=', v['name_input_id'])])
					if len(hqcl):
						hqcl[0].write(v)
						hql.add_concept()
						log += '%s\n' % line.employee_id.name
					# print("if hecl",hecl.name_input_id.name)
					else:
						self.env['hr.quincenales.conceptos.lines'].create(v)
						hql.add_concept()
						log += '%s\n' % line.employee_id.name

			self.env['hr.advance'].search([('discount_date', '>=', Lot.date_start),
										   ('discount_date', '<=', Lot.date_end),
										   ('employee_id', '=', line.employee_id.id),
										   ('state', '=', 'not payed'),
										   ('advance_type_id.id', '=', MainParameter.quin_advance_id.id)]).turn_paid_out()
		if log:
			return self.env['popup.it'].get_message('Se importo adelantos a los siguientes empleados:\n' + log)
		else:
			return self.env['popup.it'].get_message('No se importo ningun adelanto')

	def import_loans(self):
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		if not MainParameter.cts_advance_id:
			raise UserError('No se ha configurado un tipo de prestamo para Pagos Quincenales en Parametros Generales')
		log = ''
		Lot = self.payslip_run_id
		to_create = []
		for line in self.quincenales_lines:
			sql = """
					select sum(hll.amount) as amount,
					hll.employee_id,
					hlt.input_id
					from hr_loan_line hll
					inner join hr_loan_type hlt on hlt.id = hll.loan_type_id
					where hll.date >= '{0}' and
						  hll.date <= '{1}' and
						  hll.employee_id = {2} and
						  hll.validation = 'not payed' and
						  hlt.id = {3}
					group by hll.employee_id, hlt.input_id
					""".format(Lot.date_start, Lot.date_end, line.employee_id.id, MainParameter.quin_loan_id.id)
			self._cr.execute(sql)
			res_data = self._cr.dictfetchall()

			if res_data:
				hql = self.env['hr.quincenales.lines'].search([('quincenal_id', '=', self.id),('employee_id', '=', line.employee_id.id)], limit=1)
				# if len(hql):
				vals = {
						'quincenal_line_id':hql.id,
						'name_input_id': res_data[0]['input_id'],
						'amount': res_data[0]['amount'],
						'type': 'out',
					}
				to_create.append(vals)
				# print("vals if",vals)

				for v in to_create:
					hqcl = self.env['hr.quincenales.conceptos.lines'].search([('quincenal_line_id', '=', v['quincenal_line_id']),('name_input_id', '=', v['name_input_id'])])
					if len(hqcl):
						hqcl[0].write(v)
						hql.add_concept()
						log += '%s\n' % line.employee_id.name
					# print("if hecl",hecl.name_input_id.name)
					else:
						self.env['hr.quincenales.conceptos.lines'].create(v)
						hql.add_concept()
						log += '%s\n' % line.employee_id.name

			self.env['hr.loan.line'].search([('date', '>=', Lot.date_start),
											 ('date', '<=', Lot.date_end),
											 ('employee_id', '=', line.employee_id.id),
											 ('validation', '=', 'not payed'),
											 ('loan_type_id.id', '=', MainParameter.quin_loan_id.id)]).turn_paid_out()

		if log:
			return self.env['popup.it'].get_message('Se importo prestamos a los siguientes empleados:\n' + log)
		else:
			return self.env['popup.it'].get_message('No se importo ningun prestamo')

	def export_quincena(self):
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		MainParameter.check_quincena_values()
		Lot = self.payslip_run_id

		# inp_adv = MainParameter.liqui_advance_id.input_id
		# inp_loan = MainParameter.liqui_loan_id.input_id
		for line in self.quincenales_lines:
			Slip = Lot.slip_ids.filtered(lambda slip: slip.employee_id == line.employee_id)
			quin_line = Slip.input_line_ids.filtered(lambda inp: inp.input_type_id == MainParameter.quin_input_id)
			quin_line.amount = line.quincena
			for line_input in line.quincenales_conceptos_lines:
				extra_line = Slip.input_line_ids.filtered(lambda inp: inp.input_type_id == line_input.name_input_id)
				extra_line.amount = line_input.amount
				# print("codigo",extra_line.code)

		self.state = 'exported'
		return self.env['popup.it'].get_message('Se exporto exitosamente')

	def generar_excel(self):
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		output = io.BytesIO()
		basic = {'align':'left',
				 'valign':'vcenter',
				 'text_wrap':1,
				 'font_size':9,
				 'font_name':'Calibri'}
		numeric = basic.copy()
		numeric['align'] = 'right'
		numeric['num_format'] = '#,##0.00'
		numeric_int = basic.copy()
		numeric_int['align'] = 'right'
		numeric_int_bold = numeric.copy()
		numeric_int_bold['bold'] = 1
		numeric_bold = numeric.copy()
		numeric_bold['bold'] = 1
		numeric_bold['num_format'] = '#,##0.00'
		bold = basic.copy()
		bold['bold'] = 1
		header = bold.copy()
		header['bg_color'] = '#A9D0F5'
		header['border'] = 1
		header['align'] = 'center'
		title = bold.copy()
		title['font_size'] = 15
		highlight_line = basic.copy()
		highlight_line['bold'] = 1
		highlight_line['bg_color'] = '#C1E1FF'
		highlight_numeric_line = highlight_line.copy()
		highlight_numeric_line['num_format'] = '#,##0.00'
		highlight_numeric_line['align'] = 'right'
		fecha_format = basic.copy()
		fecha_format['num_format']='dd/mm/yyyy'
		direccion = MainParameter.dir_create_file
		titulo = 'Quincenal_' + str(self.fecha)

		workbook = Workbook(direccion + titulo + '.xlsx')
		worksheet = workbook.add_worksheet('Pagos Quincenales')
		# worksheet_sin_cc = workbook.add_worksheet('Sin Distribucion C.C.')
		basic_format = workbook.add_format(basic)
		bold_format = workbook.add_format(bold)
		numeric_int_format = workbook.add_format(numeric_int)
		numeric_int_bold_format = workbook.add_format(numeric_int_bold)
		numeric_format = workbook.add_format(numeric)
		numeric_bold_format = workbook.add_format(numeric_bold)
		title_format = workbook.add_format(title)
		header_format = workbook.add_format(header)
		highlight_line_format = workbook.add_format(highlight_line)
		highlight_numeric_line_format = workbook.add_format(highlight_numeric_line)
		format2 = workbook.add_format(fecha_format)

		rc = self.env.company
		worksheet.merge_range('A1:D1', rc.name if rc.name else '', title_format)
		worksheet.merge_range('A2:D2', rc.partner_id.l10n_latam_identification_type_id.name+': ' + rc.partner_id.vat, title_format)
		headers = [
			u'N° de Identificacion',
			'Nombres y Apellidos',
			'Fecha de Ingreso',
			u'Ba\u0301sico',
			u'Asignacio\u0301n Familiar',
			'Ingresos Adicionales',
			'ONP',
			'AFP Jub',
			'AFP Com.',
			'AFP Prima.',
			u'5ta Categori\u0301a',
			'Descuentos Adicionales',
			'Total',
			'Monto',
			'Ing y Desc Quincenales',
			'Quincena']
		row = 2
		col = 0
		row += 1
		for pos in range(len(headers)):
			worksheet.write(row, pos, headers[pos], header_format)

		row += 1
		for data in self.quincenales_lines:
			ing_adi = 0
			desc_adi = 0
			concepto_adi = 0
			for ing in data.quincenales_ingresos_lines:
				ing_adi += ing.monto

			for desc in data.quincenales_descuentos_lines:
				desc_adi += desc.monto

			for concepto in data.quincenales_conceptos_lines:
				concepto_adi += concepto.amount

			# print('feccha',data.fecha_ingreso)

			col = 0
			worksheet.write(row, col, data.codigo_trabajador if data.codigo_trabajador else '', basic_format)
			col += 1
			worksheet.write(row, col, data.employee_id.name if data.employee_id.name else '', basic_format)
			col += 1
			worksheet.write(row, col, data.fecha_ingreso if data.fecha_ingreso else '', format2)
			col += 1
			worksheet.write(row, col, data.basico if data.basico else 0, numeric_format)
			col += 1
			worksheet.write(row, col, data.asignacion_familiar if data.asignacion_familiar else 0, numeric_format)
			col += 1
			worksheet.write(row, col, ing_adi if ing_adi else 0, numeric_format)
			col += 1
			worksheet.write(row, col, data.onp if data.onp else 0, numeric_format)
			col += 1
			worksheet.write(row, col, data.afp_jub if data.afp_jub else 0, numeric_format)
			col += 1
			worksheet.write(row, col, data.afp_com if data.afp_com else 0, numeric_format)
			col += 1
			worksheet.write(row, col, data.afp_prima if data.afp_prima else 0, numeric_format)
			col += 1
			worksheet.write(row, col, data.quinta_cat if data.quinta_cat else 0, numeric_format)
			col += 1
			worksheet.write(row, col, desc_adi if desc_adi else 0, numeric_format)
			col += 1
			worksheet.write(row, col, data.total if data.total else 0, numeric_format)
			col += 1
			worksheet.write(row, col, data.monto if data.monto else 0, numeric_format)
			col += 1
			worksheet.write(row, col, concepto_adi if concepto_adi else 0, numeric_format)
			col += 1
			worksheet.write(row, col, data.quincena if data.quincena else 0, numeric_format)
			col += 1
			row += 1

		col_sizes = [10.0, 32.0, 10.0]
		worksheet.set_column('A:A', col_sizes[0])
		worksheet.set_column('B:B', col_sizes[1])
		worksheet.set_column('C:T', col_sizes[2])
		workbook.close()
		f = open(direccion + titulo + '.xlsx', 'rb')
		return self.env['popup.it'].get_file('Pago_quincenal.xlsx',base64.encodestring(b''.join(f.readlines())))


class hr_quincenales_lines(models.Model):
	_name = 'hr.quincenales.lines'
	_description = 'hr quincenales lines'

	quincenal_id = fields.Many2one('hr.quincenales', 'Quincena', ondelete='cascade')
	state = fields.Selection([('draft', 'Borrador'), ('exported', 'Exportado')], 'Estados', related='quincenal_id.state')
	employee_id = fields.Many2one('hr.employee', 'Empleado')
	contract_id = fields.Many2one('hr.contract', 'Contrato')
	codigo_trabajador = fields.Char(u'N° Ident')
	nombres = fields.Char('Nombres y Apellidos')
	fecha_ingreso = fields.Date('Fecha de Ing')

	basico = fields.Float(u'Ba\u0301sico')
	asignacion_familiar = fields.Float(u'Asig Fam')

	onp = fields.Float('ONP')
	afp_com = fields.Float('AFP Com.')
	afp_prima = fields.Float('AFP Prima.')
	afp_jub = fields.Float('AFP Jub')
	quinta_cat = fields.Float(u'5ta Categ')

	total = fields.Float('Total Ing', compute='compute_total')
	monto = fields.Float('Monto', compute='compute_monto')
	quincena = fields.Float('Quincena', compute='compute_quincena')

	income = fields.Float(string='(+) Ing')
	expenses = fields.Float(string='(-) Desc')

	quincenales_ingresos_lines = fields.One2many('hr.quincenales.ingresos.lines', 'quincenal_line_id', 'ingresos')
	quincenales_descuentos_lines = fields.One2many('hr.quincenales.descuentos.lines', 'quincenal_line_id', 'descuentos')
	quincenales_conceptos_lines = fields.One2many('hr.quincenales.conceptos.lines', 'quincenal_line_id', 'conceptos')

	def compute_total(self):
		for l in self:
			res = l.basico + l.asignacion_familiar - l.onp - l.afp_com - l.afp_prima - l.afp_jub - l.quinta_cat
			for i in l.quincenales_ingresos_lines:
				res += i.monto
			for i in l.quincenales_descuentos_lines:
				res -= i.monto
			l.total = res

	def compute_monto(self):
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		for l in self:
			fecha_in = l.contract_id.date_start
			dateini = str(l.quincenal_id.fecha.year) + '-' + str(l.quincenal_id.fecha.month).rjust(2, '0') + '-01'
			nfecha = datetime.datetime.strptime(dateini, '%Y-%m-%d')
			# print("nfecha",nfecha)
			# print("fecha_in",fecha_in)
			fecha_im = nfecha
			# print("fecha_im.date()",fecha_im.date())
			# if fecha_in.day != 1 and fecha_in >= fecha_im.date():
			# 	l.monto = l.total/30*abs(31-fecha_in.day) * MainParameter.percentage
			if fecha_in > nfecha.date() and fecha_in <= l.quincenal_id.fecha:
				l.monto = (l.total * (l.quincenal_id.fecha.day - fecha_in.day + 1)/ l.quincenal_id.fecha.day) * MainParameter.percentage
			else:
				l.monto = l.total * MainParameter.percentage

	def compute_quincena(self):
		for l in self:
			l.quincena = l.monto + l.income - l.expenses

	def ingresos_wizard(self):
		view_id = self.env.ref('hr_fortnightly.view_hr_quincenales_lines_ing_form', False)
		return {'type':'ir.actions.act_window',
				'res_model':'hr.quincenales.lines',
				'res_id':self.id,
				'view_id':view_id.id,
				'view_type':'form',
				'view_mode':'form',
				'views':[(view_id.id, 'form')],
				'target':'new'}

	def descuentos_wizard(self):
		view_id = self.env.ref('hr_fortnightly.view_hr_quincenales_lines_desc_form', False)
		return {'type':'ir.actions.act_window',
				'res_model':'hr.quincenales.lines',
				'res_id':self.id,
				'view_id':view_id.id,
				'view_type':'form',
				'view_mode':'form',
				'views':[(view_id.id, 'form')],
				'target':'new'}

	def conceptos_wizard(self):
		view_id = self.env.ref('hr_fortnightly.view_hr_quincenales_lines_conceptos_form', False)
		return {'type':'ir.actions.act_window',
				'res_model':'hr.quincenales.lines',
				'res_id':self.id,
				'view_id':view_id.id,
				'view_type':'form',
				'view_mode':'form',
				'views':[(view_id.id, 'form')],
				'target':'new'}

	def add_concept(self):
		In_Concepts = Out_Concepts = 0
		if self.quincenales_conceptos_lines:
			for line in self.quincenales_conceptos_lines:
				if line.type == 'in':
					In_Concepts += line.amount
				elif line.type == 'out':
					Out_Concepts += line.amount
			self.env['hr.quincenales.lines'].browse(self.id).write({'income':In_Concepts,'expenses':Out_Concepts})
		else:
			self.env['hr.quincenales.lines'].browse(self.id).write({'income':0,'expenses':0})
		return self.env['hr.quincenales'].browse(self.quincenal_id.id).quincenales_lines.refresh()

	def save_datai(self):
		self.write({})

	def save_datad(self):
		self.write({})


class hr_quincenales_ingresos_lines(models.Model):
	_name = 'hr.quincenales.ingresos.lines'
	_description = 'hr quincenales ingresos lines'

	quincenal_line_id = fields.Many2one('hr.quincenales.lines', 'Ingresos', ondelete='cascade')
	concepto_id = fields.Many2one('hr.salary.rule', 'Concepto', required=True)
	monto = fields.Float('Monto', required=True)


class hr_quincenales_descuentos_lines(models.Model):
	_name = 'hr.quincenales.descuentos.lines'
	_description = 'hr quincenales descuentos lines'

	quincenal_line_id = fields.Many2one('hr.quincenales.lines', 'Descuentos', ondelete='cascade')
	concepto_id = fields.Many2one('hr.salary.rule', 'Concepto', required=True)
	monto = fields.Float('Monto', required=True)


class hr_quincenales_conceptos_lines(models.Model):
	_name = 'hr.quincenales.conceptos.lines'
	_description = 'hr quincenales conceptos lines'

	quincenal_line_id = fields.Many2one('hr.quincenales.lines', 'Otros Conceptos', ondelete='cascade')
	name_input_id = fields.Many2one('hr.payslip.input.type', string='Descripcion')
	amount = fields.Float(string='Monto')
	type = fields.Selection([('in', 'Ingreso'),('out', 'Descuento')], string='Tipo', default='in')