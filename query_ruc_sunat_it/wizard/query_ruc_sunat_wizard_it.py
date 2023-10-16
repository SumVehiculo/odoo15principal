from odoo import models, fields, api
from odoo.exceptions import ValidationError
import xlrd
import base64
import io
class query_ruc_sunat_multi_it(models.TransientModel):
	_name="query.ruc.sunat.wizard.masiva.it"
	_description="Query RUC Sunat Masiva IT"

	name = fields.Char(default="CONSULTA RUC MASIVA",string="Nombre")
	document_file = fields.Binary(string='Excel', help="Archivo Excel")
	name_file = fields.Char(string='Nombre de Archivo') 
 
	def up_data(self):
		for i in self:
			if i.document_file:
				elem = []
				data = base64.b64decode(i.document_file)
				input_data = io.BytesIO(data)
				workbook = xlrd.open_workbook(file_contents=input_data.getvalue())
				sheet = workbook.sheet_by_index(0)
				names = [sheet.cell(row, 0).value for row in range(1, sheet.nrows)]
				query_sunat = self.env['query.ruc.sunat.it'].search([])		
				for name in names:
					new_record = query_sunat.sudo().create({
						'name': name,
					})
					elem.append(new_record.id)
				return {
					'name': 'Consulta Ruc Masiva',
					'domain' : [('id','in',elem)],
					'type': 'ir.actions.act_window',
					'res_model': 'query.ruc.sunat.it',
					'view_mode': 'tree',
					'views': [(self.env.ref('query_ruc_sunat_it.view_tree_query_ruc_sunat_it_editable').id, 'tree')],

										
				}
	def download_template(self):
		return {
			 'type' : 'ir.actions.act_url',
			 'url': '/web/binary/download_template_import_partner_lines',
			 'target': 'new',
			 }

	 
	
   

					
	