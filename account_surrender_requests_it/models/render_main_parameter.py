# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class RenderMainParameter(models.Model):
	_name = 'render.main.parameter'

	name = fields.Char(default='Parametros Principales')
	company_id = fields.Many2one('res.company',string=u'Compañía',default=lambda self: self.env.company)

	####DIARIOS####
	
	invoice_journal_id = fields.Many2one('account.journal',string=u'Diario Facturas')

	@api.constrains('company_id')
	def _check_unique_parameter(self):
		self.env.cr.execute("""select id from render_main_parameter where company_id = %d""" % (self.company_id.id))
		res = self.env.cr.dictfetchall()
		if len(res) > 1:
			raise UserError(u"Ya existen Parametros Principales para esta Compañía")