# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools

class AccountPleSaleBook(models.Model):
	_name = 'account.ple.sale.book'
	_description = 'Account Ple Sale Book'
	_auto = False
	
	periodo = fields.Char(string='Periodo', size=50)
	fecha_cont = fields.Date(string='Fecha Cont.', size=15)
	libro = fields.Char(string='Libro', size=5)
	fecha_e = fields.Date(string='Fecha Em.', size=10)
	td = fields.Char(string='TD', size=64)
	serie = fields.Char(string=u'Serie')
	numero = fields.Char(string=u'Numero') 
	estado = fields.Char(string=u'Estado')
	estado_c = fields.Char(string=u'Estado Correcto')
	am_id = fields.Many2one('account.move',string=u'Factura')

	def init(self):
		tools.drop_view_if_exists(self.env.cr, self._table)
		self.env.cr.execute('''
			CREATE OR REPLACE VIEW %s AS (
				SELECT row_number() OVER () AS id,
				a1.periodo::character varying,a1.fecha_cont,a1.libro,a1.fecha_e,a1.td,a1.serie,a1.numero,''::character varying as estado,
			'' as estado_c, a1.am_id
			from get_ventas_1_1('2019/01/01','2019/01/01',1,'pen') a1 limit 1
			)''' % (self._table,)
		)

	def view_account_move(self):

		return{

			'view_mode': 'form',
			'view_id': self.env.ref('account.view_move_form').id,
			'res_model': 'account.move',
			'type': 'ir.actions.act_window',
			'res_id': self.am_id.id,
		}

	def action_fix_ple_sale(self):
		for i in self:
			sql_update = """
				UPDATE account_move SET campo_34_sale = '%s' WHERE id = %s """ % (
					i.estado_c, str(i.am_id.id)
				)

			self.env.cr.execute(sql_update)

		return self.env['popup.it'].get_message('SE ACTUALIZARON CORRECTAMENTE LOS CAMPOS PARA PLE.')