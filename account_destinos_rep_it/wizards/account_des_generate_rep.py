# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError

class AccountDesGenerateRep(models.TransientModel):
	_name = 'account.des.generate.rep'

	name = fields.Char()
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	fiscal_year_id = fields.Many2one('account.fiscal.year',string=u'Ejercicio',required=True)
	period = fields.Many2one('account.period',string='Periodo',required=True)
	date_generate = fields.Date(string='Fecha')

	def get_report(self):

		sql = """
			DROP VIEW IF EXISTS account_des_generate_book;
			CREATE OR REPLACE view account_des_generate_book as (SELECT row_number() OVER () AS id, a1.periodo::character varying, a1.glosa, a1.cuenta, a1.name, a1.debe, a1.haber from get_asiento_destino(%s,%d) a1)""" % (
				self.period.code,self.company_id.id)

		self.env.cr.execute(sql)

		return {
			'name': 'Asiento Destino',
			'type': 'ir.actions.act_window',
			'res_model': 'account.des.generate.book',
			'view_mode': 'tree',
			'view_type': 'form',
			'views': [(False, 'tree')],
		}

	def generate_as(self):
		if not self.date_generate:
			raise UserError("Debe completar el Campo Fecha")

		destination_journal = self.env['account.main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).destination_journal

		if not destination_journal:
			raise UserError(u'No existe un Diario Asiento Automático configurado en Parametros Generales de Contabilidad para su Compañía.')

		if self.date_generate < self.period.date_start or self.date_generate > self.period.date_end:
		 	raise UserError('Fecha fuera del rango del periodo seleccionado.')

		asiento_delete = self.env['account.move'].search([('automatic_destiny','=',True),('date','>=',self.period.date_start),('date','<=',self.period.date_end),('company_id','=',self.company_id.id)])
		if asiento_delete or len(asiento_delete)>0:

			for move in asiento_delete:
				move.button_cancel()
				move.line_ids.unlink()
				move.name = "/"
				move.unlink()
		
		sql = """select * from get_asiento_destino(%s,%d)""" % (self.period.code,self.company_id.id)
		self.env.cr.execute(sql)
		obj =self.env.cr.fetchall()

		lineas = []

		for elemnt in obj:
			vals = (0,0,{
				'name': elemnt[1],
				'debit': elemnt[4],
				'credit': elemnt[5], 
				'date': self.date_generate,
				'account_id': elemnt[6],
				'nro_comp': 'DEST-'+self.period.code,
				'company_id': self.company_id.id,
			})
			lineas.append(vals)
			
		move_id = self.env['account.move'].create({
			'company_id': self.company_id.id,
			'journal_id': destination_journal.id,
			'date': self.date_generate,
			'automatic_destiny':True,
			'ref': 'DEST-'+self.period.code, 
			'glosa': 'Por el destino del Periodo '+self.period.code,
			'line_ids':lineas})

		if move_id.state == "draft":
			move_id.post()

		return {
			'view_mode': 'form',
			'view_id': self.env.ref('account.view_move_form').id,
			'res_model': 'account.move',
			'type': 'ir.actions.act_window',
			'res_id': move_id.id,
		}