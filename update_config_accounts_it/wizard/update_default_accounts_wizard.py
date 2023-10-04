# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError

class UploadChartAccountIt(models.TransientModel):
	_name = "update.default.accounts.wizard"

	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	property_account_receivable_id = fields.Many2one('account.account',string='Cuenta a cobrar (Contactos)')
	property_account_payable_id = fields.Many2one('account.account',string='Cuenta a pagar (Contactos)')
	property_account_expense_categ_id = fields.Many2one('account.account',string='Cuenta de gasto (Categoría de Producto)')
	property_account_income_categ_id = fields.Many2one('account.account',string='Cuenta de Ingreso (Categoría de Producto)')
	property_account_income_id = fields.Many2one('account.account',string='Cuenta de Ingreso (Producto)')
	property_account_expense_id = fields.Many2one('account.account',string='Cuenta de gasto (Producto)')
	property_stock_account_output_categ_id = fields.Many2one('account.account',string='Cuenta de salida de stock (Categoría de Producto)')
	property_stock_account_input_categ_id = fields.Many2one('account.account',string='Cuenta de entrada de stock (Categoría de Producto)')
	property_stock_valuation_account_id = fields.Many2one('account.account',string='Cuenta de valoración de stock (Categoría de Producto)')

	def update_account(self):
		model = 'account.account,'
		if self.property_account_receivable_id:
			gl = self.env['ir.property'].search([('name','=','property_account_receivable_id'),('res_id','=',False),('company_id','=',self.company_id.id)],limit=1)
			gl.write({'value_reference': model+str(self.property_account_receivable_id.id)})

		if self.property_account_payable_id:
			en = self.env['ir.property'].search([('name','=','property_account_payable_id'),('res_id','=',False),('company_id','=',self.company_id.id)],limit=1)
			en.write({'value_reference': model+str(self.property_account_payable_id.id)})

		if self.property_account_expense_categ_id:
			da = self.env['ir.property'].search([('name','=','property_account_expense_categ_id'),('res_id','=',False),('company_id','=',self.company_id.id)],limit=1)
			da.write({'value_reference': model+str(self.property_account_expense_categ_id.id)})

		if self.property_account_income_categ_id:
			ju = self.env['ir.property'].search([('name','=','property_account_income_categ_id'),('res_id','=',False),('company_id','=',self.company_id.id)],limit=1)
			ju.write({'value_reference': model+str(self.property_account_income_categ_id.id)})

		if self.property_account_expense_id:
			lia = self.env['ir.property'].search([('name','=','property_account_expense_id'),('res_id','=',False),('company_id','=',self.company_id.id)],limit=1)
			lia.write({'value_reference': model+str(self.property_account_expense_id.id)})

		if self.property_stock_account_output_categ_id:
			mer = self.env['ir.property'].search([('name','=','property_stock_account_output_categ_id'),('res_id','=',False),('company_id','=',self.company_id.id)],limit=1)
			mer.write({'value_reference': model+str(self.property_stock_account_output_categ_id.id)})

		if self.property_stock_account_input_categ_id:
			ma = self.env['ir.property'].search([('name','=','property_stock_account_input_categ_id'),('res_id','=',False),('company_id','=',self.company_id.id)],limit=1)
			ma.write({'value_reference': model+str(self.property_stock_account_input_categ_id.id)})

		if self.property_stock_valuation_account_id:
			yh = self.env['ir.property'].search([('name','=','property_stock_valuation_account_id'),('res_id','=',False),('company_id','=',self.company_id.id)],limit=1)
			yh.write({'value_reference': model+str(self.property_stock_valuation_account_id.id)})
		
		if self.property_account_income_id:
			ua = self.env['ir.property'].search([('name','=','property_account_income_id'),('res_id','=',False),('company_id','=',self.company_id.id)],limit=1)
			ua.write({'value_reference': model+str(self.property_account_income_id.id)})
		
		return self.env['popup.it'].get_message('SE ACTUALIZARON LAS CUENTAS PREDETERMINADAS.')