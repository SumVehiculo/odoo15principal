# -*- coding: utf-8 -*-

import binascii
import tempfile
import xlrd
from odoo import fields, models, _
from odoo.exceptions import ValidationError
from datetime import datetime

class bank_loans_lines_import(models.TransientModel):
	_name = 'bank.loans.lines.import'
	_description = 'Importador Lineas de Prestamos Wizard'
	

	loan_id = fields.Many2one('bank.loans', string='Prestamo')
	file = fields.Binary('Archivo')
	name_file = fields.Char('name_file')

	def importar(self):
		if self:
			try:
				file_string = tempfile.NamedTemporaryFile(suffix=".xlsx")
				file_string.write(binascii.a2b_base64(self.file))
				book = xlrd.open_workbook(file_string.name)
				sheet = book.sheet_by_index(0)
			except:
				raise ValidationError(_("Por favor elija el archivo correcto"))
			starting_line = True
			cont=0
			for i in range(sheet.nrows):
				if starting_line:
					starting_line = False
				else:
					line = list(sheet.row_values(i))
					cont+=1
					
					if line[0] or line[1] or line[2] or line[3] or line[4] or line[5]:		
						date_str = str(line[1])
						date_obj = datetime.strptime(date_str, "%d/%m/%Y").date()										
						self.env['bank.loans.lines'].sudo().create({
							'loan_id': self.loan_id.id,
							'month': line[0],
							'date':date_obj,
							'amount_amort': line[2],
							'inters': line[3],
							'quota': line[4],
							'amount_debt':line[5]
						})						
					else:
						raise ValidationError(_('EN LA FILA %s FALTA DATOS'%(str(cont))))
			return self.env['popup.it'].get_message('SE IMPORTARON CORRECTAMENTE SUS LINEAS DE PRESTAMO')


	def download_template(self):
		return {
			 'type' : 'ir.actions.act_url',
			 'url': '/web/binary/download_template_import_loans_lines',
			 'target': 'new',
			 }
