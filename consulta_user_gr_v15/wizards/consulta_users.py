# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
import base64

class ConsultaUsuariosWizard(models.Model):
	_name = 'consulta.usuarios.wizard'

	def grupos_acceso(self):
		import io
		from xlsxwriter.workbook import Workbook
		output = io.BytesIO()

		direccion = self.env['account.main.parameter'].search([])[0].dir_create_file
		workbook = Workbook(direccion +'reporte_lista_grupos_accesso.xlsx')
		worksheet = workbook.add_worksheet("Lista grupos de accesso")
		bold = workbook.add_format({'bold': True})
		bold.set_font_size(8)
		normal = workbook.add_format()
		boldbord = workbook.add_format({'bold': True})
		boldbord.set_border(style=2)
		boldbord.set_align('center')
		boldbord.set_align('vcenter')
		boldbord.set_text_wrap()
		boldbord.set_font_size(8)
		boldbord.set_bg_color('#DCE6F1')

		especial1 = workbook.add_format({'bold': True})
		especial1.set_align('center')
		especial1.set_align('vcenter')
		especial1.set_text_wrap()
		especial1.set_font_size(15)

		numbertres = workbook.add_format({'num_format':'0.000'})
		numberdos = workbook.add_format({'num_format':'0.00'})
		numberseis = workbook.add_format({'num_format':'0.000000'})
		numberseis.set_font_size(8)
		numberocho = workbook.add_format({'num_format':'0.00000000'})
		numberocho.set_font_size(8)
		bord = workbook.add_format()
		bord.set_border(style=1)
		bord.set_font_size(8)
		numberdos.set_border(style=1)
		numberdos.set_font_size(8)
		numbertres.set_border(style=1)
		numberseis.set_border(style=1)
		numberocho.set_border(style=1)
		numberdosbold = workbook.add_format({'num_format':'0.00','bold':True})
		numberdosbold.set_font_size(8)

		
		tam_col = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
		worksheet.merge_range(1,0,1,4, "LISTA DE GRUPOS DE ACCESO", especial1)
		worksheet.write(2,1,'NOMBRE DE USUARIO',boldbord)
		worksheet.write(2,2,'CORREO DE USUARIO',boldbord)
		worksheet.write(2,3,'CATEGORIA DE PERMISO',boldbord)
		worksheet.write(2,4,'GRUPO DE ACCESO',boldbord)
		
		x= 3
		for i in self.env['res.users'].sudo().search([]):
			compania = ""
			for l in i.company_ids:
				compania += l.name + ','

			for c in self.env['ir.module.category'].sudo().search([]):
				for y in self.env['res.groups'].sudo().search([('category_id','=',c.id)]):
					if i.id in y.users.ids:
						worksheet.write(x,1,i.name or '' ,bord )
						worksheet.write(x,2,i.email or '' ,bord )
						worksheet.write(x,3,c.name or '' ,bord )
						worksheet.write(x,4,y.name or '' ,bord )
						x = x +1
						tam_col = [5,25,25,20,40,5,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11]

					else:
						x = x
		
		worksheet.set_column('A:A', tam_col[0])
		worksheet.set_column('B:B', tam_col[1])
		worksheet.set_column('C:C', tam_col[2])
		worksheet.set_column('D:D', tam_col[3])
		worksheet.set_column('E:E', tam_col[4])
		worksheet.set_column('F:F', tam_col[5])
		worksheet.set_column('G:G', tam_col[6])
		worksheet.set_column('H:H', tam_col[7])
		worksheet.set_column('I:I', tam_col[8])
		worksheet.set_column('J:J', tam_col[9])
		worksheet.set_column('K:K', tam_col[10])
		worksheet.set_column('L:L', tam_col[11])
		worksheet.set_column('M:M', tam_col[12])
		worksheet.set_column('N:N', tam_col[13])
		worksheet.set_column('O:O', tam_col[14])
		worksheet.set_column('P:P', tam_col[15])
		worksheet.set_column('Q:Q', tam_col[16])
		worksheet.set_column('R:R', tam_col[17])
		worksheet.set_column('S:S', tam_col[18])
		worksheet.set_column('T:Z', tam_col[19])

		workbook.close()


		f = open(direccion + 'reporte_lista_grupos_accesso.xlsx', 'rb')

		return self.env['popup.it'].get_file('reporte_lista_grupos_accesso.xlsx',base64.encodestring(b''.join(f.readlines())))


	def user_company(self):
			import io
			from xlsxwriter.workbook import Workbook
			output = io.BytesIO()

			direccion = self.env['account.main.parameter'].search([])[0].dir_create_file
			workbook = Workbook(direccion +'reporte_lista_usuarios.xlsx')
			worksheet = workbook.add_worksheet("Lista grupos de accesso")
			bold = workbook.add_format({'bold': True})
			bold.set_font_size(8)
			normal = workbook.add_format()
			boldbord = workbook.add_format({'bold': True})
			boldbord.set_border(style=2)
			boldbord.set_align('center')
			boldbord.set_align('vcenter')
			boldbord.set_text_wrap()
			boldbord.set_font_size(8)
			boldbord.set_bg_color('#DCE6F1')

			especial1 = workbook.add_format({'bold': True})
			especial1.set_align('center')
			especial1.set_align('vcenter')
			especial1.set_text_wrap()
			especial1.set_font_size(15)

			numbertres = workbook.add_format({'num_format':'0.000'})
			numberdos = workbook.add_format({'num_format':'0.00'})
			numberseis = workbook.add_format({'num_format':'0.000000'})
			numberseis.set_font_size(8)
			numberocho = workbook.add_format({'num_format':'0.00000000'})
			numberocho.set_font_size(8)
			bord = workbook.add_format()
			bord.set_border(style=1)
			bord.set_font_size(8)
			numberdos.set_border(style=1)
			numberdos.set_font_size(8)
			numbertres.set_border(style=1)
			numberseis.set_border(style=1)
			numberocho.set_border(style=1)
			numberdosbold = workbook.add_format({'num_format':'0.00','bold':True})
			numberdosbold.set_font_size(8)

			
			tam_col = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
			worksheet.merge_range(1,0,1,4, "LISTA DE USUARIOS", especial1)
			worksheet.write(2,1,'NOMBRE DE USUARIO',boldbord)
			worksheet.write(2,2,'CORREO DE USUARIO',boldbord)
			worksheet.write(2,3,'COMPAÑIAS DE ACCESO',boldbord)
			
			x= 3
			for i in self.env['res.users'].sudo().search([]):
				compania = ""
				for l in i.company_ids:
					compania += l.name + ','
				worksheet.write(x,1,i.name or '' ,bord )
				worksheet.write(x,2,i.email or '' ,bord )
				worksheet.write(x,3,compania or '' ,bord )
				x = x +1
				tam_col = [5,25,25,50,5,5,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11]

		
			
			worksheet.set_column('A:A', tam_col[0])
			worksheet.set_column('B:B', tam_col[1])
			worksheet.set_column('C:C', tam_col[2])
			worksheet.set_column('D:D', tam_col[3])
			worksheet.set_column('E:E', tam_col[4])
			worksheet.set_column('F:F', tam_col[5])
			worksheet.set_column('G:G', tam_col[6])
			worksheet.set_column('H:H', tam_col[7])
			worksheet.set_column('I:I', tam_col[8])
			worksheet.set_column('J:J', tam_col[9])
			worksheet.set_column('K:K', tam_col[10])
			worksheet.set_column('L:L', tam_col[11])
			worksheet.set_column('M:M', tam_col[12])
			worksheet.set_column('N:N', tam_col[13])
			worksheet.set_column('O:O', tam_col[14])
			worksheet.set_column('P:P', tam_col[15])
			worksheet.set_column('Q:Q', tam_col[16])
			worksheet.set_column('R:R', tam_col[17])
			worksheet.set_column('S:S', tam_col[18])
			worksheet.set_column('T:Z', tam_col[19])

			workbook.close()


			f = open(direccion + 'reporte_lista_usuarios.xlsx', 'rb')

			return self.env['popup.it'].get_file('reporte_lista_usuarios.xlsx',base64.encodestring(b''.join(f.readlines())))


