# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError

class HrEmployee(models.Model):
	_inherit = 'hr.employee'

	type_document_id = fields.Many2one('hr.type.document', string='Tipo de Documento')
	wage_bank_account_id = fields.Many2one('res.partner.bank', string='Cuenta Sueldo')
	cts_bank_account_id = fields.Many2one('res.partner.bank', string='Cuenta CTS')
	bank_export_paymet = fields.Many2one('res.bank','Banco para Sueldos', related="wage_bank_account_id.bank_id", store=True)
	bank_export_cts = fields.Many2one('res.bank','Banco para CTS', related="cts_bank_account_id.bank_id", store=True)
	names = fields.Char(string='Nombres')
	last_name = fields.Char(string='Apellido Paterno')
	m_last_name = fields.Char(string='Apellido Materno')
	# is_manager = fields.Boolean(string='Es un Director', default=False)
	condition = fields.Selection([('domiciled', 'Domiciliado'),
								  ('not_domiciled', 'No Domiciliado')], string='Condicion', default='domiciled')
	# men = fields.Integer(string='Hijos Hombres')
	# women = fields.Integer(string='Hijos Mujeres')
	address = fields.Char(string=u'Domicilio')

	@api.onchange('names', 'last_name', 'm_last_name')
	def verify_name(self):
		self.name = '%s %s %s' % ((self.last_name or '').strip(), (self.m_last_name or '').strip(),(self.names or '').strip())

	def name_get(self):
		result = []
		for employee in self:
			name = '%s %s %s' % ((employee.last_name or '').strip(), (employee.m_last_name or '').strip(),(employee.names or '').strip())
			result.append([employee.id, name])
		return result

	@api.constrains('type_document_id','identification_id','company_id')
	def _verify_employee_per_company(self):
		log = ''
		for i in self:
			if i.type_document_id.id and i.identification_id:
				if not i.company_id.id:
					for reps in i.env["hr.employee"].sudo().search([("type_document_id","=",i.type_document_id.id),
																	("identification_id","=",i.identification_id)]):
						if reps.id != i.id:
							log += '%s \n' % str(reps.name)
				else:
					for reps in i.env["hr.employee"].sudo().search([("type_document_id","=",i.type_document_id.id),
																	("identification_id","=",i.identification_id),"|",
																	("company_id","=",i.company_id.id),("company_id","=",False)]):
						if reps.id != i.id:
							log += '%s \n' % str(reps.name)
		if log:
			raise UserError('Los siguientes empleados ya existen en el sistema:\n' + log)