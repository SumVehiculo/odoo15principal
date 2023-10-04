# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
import subprocess
import sys
import requests
import time
import re

def install(package):
	subprocess.check_call([sys.executable, "-m", "pip", "install", package])


try:
	from suds.client import Client
except:
	install('suds-py3')

try:
	from bs4 import BeautifulSoup
except Exception as e:
	install('beautifulsoup4')
	from bs4 import BeautifulSoup


class ResPartner(models.Model):
	_inherit = 'res.partner'
	state_id = fields.Many2one('res.country.state', string='Departamento')
	province_id = fields.Many2one('res.country.state', string='Provincia')
	district_id = fields.Many2one('res.country.state', string='Distrito')

	####### CONSULTA DNI #########
	related_identification = fields.Char(related='l10n_latam_identification_type_id.code_sunat', store=True)
	n2_actv_econ = fields.Char(string='# Actividad Economica (A.C)')
	n2_actv_econ_1 = fields.Char(string='A.C Principal')
	n2_actv_econ_2 = fields.Char(string='A.C Secundaria 1')
	n2_actv_econ_3 = fields.Char(string='A.C Secundaria 2')
	n2_init_actv = fields.Char(string='Inicio de Actividad')
	n2_act_com_ext = fields.Char(string='Inicio de Actividad de Comercio Exterior')
	n2_afi_ple = fields.Char(string='Fecha Afiliacion al PLE')
	n2_cp_auto = fields.Char(string='Comprobantes autorizados')
	n2_dir_fiscal = fields.Char(string='Direccion Fiscal')
	n2_nom_comer = fields.Char(string='Nombre Comercial')
	n2_padrones = fields.Char(string='Padron')
	n2_sis_contab = fields.Char(string='Tipo de Sistema Contable')
	n2_see = fields.Char(string='Sistema de Emision Electronica')
	n2_tipo_contr = fields.Char(string='Tipo de Contrato')
	is_partner_retencion = fields.Boolean(string="Agente de Retención")
	direccion_complete_it = fields.Char(compute="get_adreess_it",string="Direccion Completa")
	direccion_complete_ubigeo_it = fields.Char(compute="get_adreess_it",string="Direccion Completa Ubigeo")

	#SE ESTA COPIANDO LOS CAMPOS DEL ACCOUNT_FIELDS_IT PARA QUE EL MODULO QUERY_RUC_DNI SEA LIBRE E INDEPENDIENTE
	name_p = fields.Char(string='Nombres',size=200)
	last_name = fields.Char(string='Apellido Paterno',size=200)
	m_last_name = fields.Char(string='Apellido Materno',size=200)
	
	@api.onchange('district_id')
	def change_distrito(self):
		for record in self:
			record.zip = record.district_id.code

	@api.depends('street', 'state_id','province_id', 'district_id', 'country_id', 'zip')
	def get_adreess_it(self):
		for record in self:
			direccioni = direccionf = record.street or ''
			if record.state_id or record.province_id or record.district_id or record.country_id:
				dep_pro_dis = f"{record.state_id.name or ''} - {record.province_id.name or ''} - {record.district_id.name or '' }"
				direccioni += ' ' + (dep_pro_dis if dep_pro_dis  else '' ) + ' , ' + (record.country_id.name if record.country_id else '')
				direccionf += ' ' + dep_pro_dis + ' , ' + (record.zip or '') + '  , ' + (record.country_id.name or '')
			record.direccion_complete_it = direccioni
			record.direccion_complete_ubigeo_it = direccionf

	@api.model
	def default_get(self, fields):
		res = super(ResPartner, self).default_get(fields)
		if 'name' not in res:
			res['name'] = 'Nombre'
		res['name_p'] = 'Nombre'
		res['last_name'] = 'Apellido Paterno'
		res['m_last_name'] = 'Apellido Materno'
		return res

	@api.onchange('company_type')
	def _set_street_default(self):
		if self.company_type == 'company':
			if self.l10n_latam_identification_type_id:
				if self.l10n_latam_identification_type_id.code_sunat == '6':
					self.street = 'Calle'
		else:
			self.street = ''

	@api.onchange('l10n_latam_identification_type_id')
	def _verify_document(self):
		if self.l10n_latam_identification_type_id:
			if self.l10n_latam_identification_type_id.code_sunat == '6' and self.company_type == 'company':
				self.street = 'Calle'
			else:
				self.street = ''
		else:
			self.street = ''

	def verify_dni(self):

		parameters = self.env['ruc.main.parameter'].verify_query_parameters()
		if not self.vat:
			raise UserError("Debe ingresar un DNI")
		if parameters.query_supplier == '1':
			client = Client(parameters.query_dni_url, faults=False, cachingpolicy=1, location=parameters.query_dni_url)
			try:
				result = client.service.consultar(self.vat, parameters.query_email, parameters.query_token,
												parameters.query_type)
			except Exception as e:
				raise UserError('No se encontro el DNI')
			texto = result[1].split('|')
			nombres = ''
			a_paterno = ''
			a_materno = ''

			for c in texto:
				tmp = c.split('=')
				if tmp[0] == 'status_id' and tmp[1] == '102':
					raise UserError('El DNI debe tener al menos 8 digitos de longitud')
				if tmp[0] == 'status_id' and tmp[1] == '103':
					raise UserError('El DNI debe ser un valor numerico')
				if tmp[0] == 'reniec_nombres' and tmp[1] != '':
					nombres = tmp[1]
					self.name_p = tmp[1]
				if tmp[0] == 'reniec_paterno' and tmp[1] != '':
					a_paterno = tmp[1]
					self.last_name = tmp[1]
				if tmp[0] == 'reniec_materno' and tmp[1] != '':
					a_materno = tmp[1]
					self.m_last_name = tmp[1]
			self.name = (nombres + " " + a_paterno + " " + a_materno).strip()
		elif parameters.query_supplier == '2':
			params = {
						"token": parameters.migo_token,
						"dni": self.vat
					}
			
			url = 'https://api.migo.pe/api/v1/dni'
			
			headers = requests.utils.default_headers()
			headers['Content-Type'] = 'application/json'
			headers['Accept'] = 'application/json'
			try:
				response = requests.post(url, headers=headers, params=params)
				jsson = response.json() #response.text
				flag = jsson['success']

			except Exception as err:
				raise UserError(err)
			
			if flag:
				if jsson['nombre']:
					nombres = jsson['nombre'].split(' ')
					a_paterno = nombres[0]
					self.last_name = nombres[0]
					a_materno = nombres[1]
					self.m_last_name = nombres[1]
					nombres = jsson['nombre'].replace(a_paterno+ ' '+a_materno+' ','')
					self.name_p = jsson['nombre'].replace(a_paterno+ ' '+a_materno+' ','')
					self.name = (nombres + " " + a_paterno + " " + a_materno).strip()
		else:
			raise UserError(u'Servicio no disponible de búsqueda DNI para SUNAT, debe escoger otro proveedor de CONSULTA RUC/DNI')
			

	####### CONSULTA DNI #########

	####### CONSULTA RUC #########
	ruc_state = fields.Char(string='RUC Estado')
	ruc_condition = fields.Char(string=u'RUC Condición')

	def verify_ruc(selfs):
		for self in selfs:
			if self.l10n_latam_identification_type_id.code_sunat == '6':
				parameters = self.env['ruc.main.parameter'].verify_query_parameters()
				if parameters.query_supplier == '1':
					client = Client(parameters.query_ruc_url, faults=False, cachingpolicy=1,
									location=parameters.query_ruc_url)
					result = client.service.consultaRUC(self.vat, parameters.query_email, parameters.query_token,
														parameters.query_type)
					texto = result[1].split('|')
					flag = False
					for i in texto:
						tmp = i.split('=')
						if tmp[0] == 'status_id' and tmp[1] == '1':
							flag = True

					# obtner el distrito - provincia - departamento
					departamento_string = provincia_string = distrito_string = dep_pro_dis = None
					for j in texto:
						tmp = j.split('=')
						if tmp[0] == 'n1_ubigeo_dep':
							departamento_string = tmp[1]
						if tmp[0] == 'n1_ubigeo_pro':
							provincia_string = tmp[1]
						if tmp[0] == 'n1_ubigeo_dis':
							distrito_string = tmp[1]
					if departamento_string and provincia_string and distrito_string:
						dep_pro_dis = f"{departamento_string} - {provincia_string} - {distrito_string}"

					if flag:
						for j in texto:
							tmp = j.split('=')
							if tmp[0] == 'n1_alias':
								self.name = tmp[1]
							if tmp[0] == 'n1_direccion':
								# obtener la direccion
								direccionx = tmp[1]
								# quitar el pais - distrito - departamento
								if dep_pro_dis:
									direccionx = direccionx.replace(dep_pro_dis, '')
								# raise ValueError(direccionx)
								self.street = direccionx

							for ar in ['n2_actv_econ', 'n2_actv_econ_1', 'n2_actv_econ_2', 'n2_actv_econ_3',
									'n2_init_actv',
									'n2_act_com_ext', 'n2_tipo_contr',
									'n2_afi_ple', 'n2_cp_auto', 'n2_dir_fiscal', 'n2_nom_comer',
									'n2_padrones', 'n2_sis_contab', 'n2_see']:
								if tmp[0] == ar:
									self[ar] = str(tmp[1])

							if tmp[0] == 'n1_ubigeo':
								ubi_t = tmp[1]
								ubigeo = self.env['res.country.state'].search([('code', '=', ubi_t)])

								if ubigeo:
									self.zip = tmp[1]
									pais = self.env['res.country'].search([('code', '=', 'PE')])
									ubidepa = ubi_t[0:2]
									ubiprov = ubi_t[0:4]
									ubidist = ubi_t[0:6]

									departamento = self.env['res.country.state'].search(
										[('code', '=', ubidepa), ('country_id', '=', pais.id)])
									provincia = self.env['res.country.state'].search(
										[('code', '=', ubiprov), ('country_id', '=', pais.id)])
									distrito = self.env['res.country.state'].search(
										[('code', '=', ubidist), ('country_id', '=', pais.id)])

									self.country_id = pais.id
									self.state_id = departamento.id
									self.province_id = provincia.id
									self.district_id = distrito.id
							if tmp[0] == 'n1_estado':
								self.ruc_state = tmp[1]
							if tmp[0] == 'n1_condicion':
								self.ruc_condition = tmp[1]

					else:
						raise UserError("El RUC es invalido.")
				elif parameters.query_supplier == '2':
					params = {
								"token": parameters.migo_token,
								"ruc": self.vat
							}
					
					url = 'https://api.migo.pe/api/v1/ruc'
					url_actividad = 'https://api.migo.pe/api/v1/ruc/actividad/{ruc}?token={token}'.format(ruc = self.vat,token = parameters.migo_token)
					
					headers = requests.utils.default_headers()
					headers['Content-Type'] = 'application/json'
					headers['Accept'] = 'application/json'
					try:
						response = requests.post(url, headers=headers, params=params)
						response_actividad = requests.get(url_actividad, headers=headers)
						jsson = response.json() #response.text
						jsson_actividad = response_actividad.json() #response.text
						flag = jsson['success']
						flag_actividad = jsson_actividad['success']

					except Exception as err:
						raise UserError(err)
					
					if flag:
						if jsson['nombre_o_razon_social']:
							self.name = jsson['nombre_o_razon_social']
						if jsson['direccion_simple']:
							self.street = jsson['direccion_simple']
						if jsson['ubigeo'] != '-':
							ubigeo=self.env['res.country.state'].search([('code','=',jsson['ubigeo'])])
							if ubigeo:
								self.zip = jsson['ubigeo']
								pais =self.env['res.country'].search([('code','=','PE')]) 
								ubidepa=jsson['ubigeo'][0:2]
								ubiprov=jsson['ubigeo'][0:4]
								ubidist=jsson['ubigeo'][0:6]

								departamento = self.env['res.country.state'].search([('code','=',ubidepa),('country_id','=',pais.id)])
								provincia  = self.env['res.country.state'].search([('code','=',ubiprov),('country_id','=',pais.id)])
								distrito = self.env['res.country.state'].search([('code','=',ubidist),('country_id','=',pais.id)])

								self.country_id=pais.id
								self.state_id=departamento.id
								self.province_id = provincia.id
								self.district_id = distrito.id
						if jsson['estado_del_contribuyente']:
							self.ruc_state = jsson['estado_del_contribuyente']
						if jsson['condicion_de_domicilio']:
							self.ruc_condition = jsson['condicion_de_domicilio']
							
					else:
						raise UserError("El RUC es invalido.")
					if flag_actividad:
						if jsson_actividad['actividad_economica_rev3_principal']:
							self.n2_actv_econ_1 = jsson_actividad['actividad_economica_rev3_principal']
							self.n2_actv_econ_2 = jsson_actividad['actividad_economica_rev3_secundaria']
							self.n2_actv_econ_3 = jsson_actividad['actividad_economica_rev4_principal']

				else:
					if not self.check_ruc(self.vat): 
						raise UserError(u"La entrada no es un número de RUC valido.")
					content_ruc=self.get_data(self.vat)
					if len(content_ruc)!=18:
						raise UserError(u"El número de RUC no existe.")
					self.name = content_ruc[0].split("-")[1].strip()
					self.street = content_ruc[7]
					self.n2_nom_comer=content_ruc[2]
					self.ruc_state = content_ruc[5]
					self.ruc_condition = content_ruc[6]
					self.n2_sis_contab = content_ruc[10]
					self.n2_see=content_ruc[13]
					self.is_partner_retencion = u"Incorporado al Régimen de Agentes de Retención" in content_ruc[17]

					act_eco = content_ruc[11].split("\n")
					self.n2_actv_econ = str(len(act_eco))
					self.n2_actv_econ_1 = act_eco[0]
					self.n2_actv_econ_2 = act_eco[1] if len(act_eco)>1 else ''
					self.n2_actv_econ_3 = act_eco[2] if len(act_eco)>2 else ''
					self.n2_init_actv = content_ruc[4]
					self.n2_afi_ple = content_ruc[16]
					self.n2_padrones = content_ruc[17]
					self.n2_tipo_contr = content_ruc[1]

	####### CONSULTA RUC #########

	def check_ruc(self,ruc):
		return re.fullmatch(r'\d{8}-\d|\d{11}', ruc) is not None
	
	def get_data(self,ruc):
		respuesta_resultado_ruc = []

		headers = {
			"Host": "e-consultaruc.sunat.gob.pe",
			"sec-ch-ua": "\" Not A;Brand\";v=\"99\", \"Chromium\";v=\"90\", \"Google Chrome\";v=\"90\"",
			"sec-ch-ua-mobile": "?0",
			"Sec-Fetch-Dest": "document",
			"Sec-Fetch-Mode": "navigate",
			"Sec-Fetch-Site": "none",
			"Sec-Fetch-User": "?1",
			"Upgrade-Insecure-Requests": "1",
			"User-Agent": "Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36"
		}
		time.sleep(0.1)

		s = requests.Session()
		url = "https://e-consultaruc.sunat.gob.pe/cl-ti-itmrconsruc/jcrS00Alias"
		payload={}
		resultadoConsulta=s.request("GET",url,headers=headers,data=payload,verify=True)
		# Error de conexion
		if(resultadoConsulta.status_code!=200):
			print("error de conexion")

		time.sleep(0.1)
		headers["Origin"]="https://e-consultaruc.sunat.gob.pe"
		headers["Referer"]=url
		headers["Sec-Fetch-Site"]="same-origin"

		numero_dni = "12345678" 
		data = {
			"accion": "consPorTipdoc",
			"razSoc": "",
			"nroRuc": "",
			"nrodoc": numero_dni,
			"contexto": "ti-it",
			"modo": "1",
			"search1": "",
			"rbtnTipo": "2",
			"tipdoc": "1",
			"search2": numero_dni,
			"search3": "",
			"codigo": ""
		}
		resultadoConsultaRandom=s.request("POST",url,headers=headers,data=data,verify=True)
		# Error de conexion
		if resultadoConsultaRandom.status_code!=200 :
			print("error de conexion")

		time.sleep(0.1)
		soup = BeautifulSoup(resultadoConsultaRandom.text, 'html.parser')
		numero_random = soup.find('input', {'type': 'hidden', 'name': 'numRnd'})['value']
		data = {
			"accion": "consPorRuc",
			"actReturn": "1",
			"nroRuc": ruc,
			"numRnd": numero_random,
			"modo": "1"
		}
		soup=None
		# Por si cae en el primer intento por el código "Unauthorized", en el bucle se va a intentar hasta 3 veces "nConsulta"
		cConsulta = 0
		nConsulta = 3
		codigo_estado = 401
		while cConsulta < nConsulta and codigo_estado == 401:
			with s.request("POST",url,headers=headers,data=data,verify=True) as resultadoConsultaDatos:
				if resultadoConsultaDatos.status_code!=200:
					cConsulta+=1
					continue
				pattern = re.compile(r"<!--(.*?)-->", re.DOTALL)
				html_without_comments = re.sub(pattern, "", resultadoConsultaDatos.text)

				soup=BeautifulSoup(html_without_comments,'html.parser')
				text_list=soup.findAll('div', class_="row")
				text_list.pop(0)
				text_list=text_list[0:16]
				for data in text_list:
					if(str(data).find("col-sm-3")!=-1):
						col_sm_3=data.findAll('div',class_="col-sm-3")
						for d in range(1,len(col_sm_3),2):
							respuesta_resultado_ruc.append(col_sm_3[d].get_text(strip=True))
					elif(str(data).find("table")!=-1):
						table_td=data.findAll('td')
						table_td=[td.get_text(strip=True) for td in table_td]
						table_td=[' '.join(td.split()) for td in table_td]
						respuesta_resultado_ruc.append('\r\n'.join(table_td))
					elif(str(data).find("list-group-item-text")!=-1):
						result=data.find('p', class_='list-group-item-text')
						result=result.get_text(strip=True)
						result=' '.join(result.split())
						respuesta_resultado_ruc.append(result)
					else:
						result=data.findAll('h4', class_='list-group-item-heading')
						if len(result)==2:
							respuesta_resultado_ruc.append(result[1].get_text(strip=True))
						else:
							result=data.find('div',class_='col-sm-7')
							respuesta_resultado_ruc.append(result.get_text(strip=True))
				if ruc[:2] == '10':
					for c,res in enumerate(respuesta_resultado_ruc):
						if c >= 3:
							respuesta_resultado_ruc[c] = respuesta_resultado_ruc[c+1] if c < len(respuesta_resultado_ruc)-1 else 'NIGUNO'
				return respuesta_resultado_ruc