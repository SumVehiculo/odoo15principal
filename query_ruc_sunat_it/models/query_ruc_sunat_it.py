from odoo import models, fields, _
from odoo.exceptions import ValidationError
class QueryRucSUnatIT(models.Model):
	_name="query.ruc.sunat.it"
	_description="Query RUC Sunat IT"

	name = fields.Char(string="RUC")


	numero_ruc=fields.Text(string="Número de RUC:", readonly=True)
	tipo_contribuyente=fields.Text(string="Tipo de Contribuyente:", readonly=True)
	nombre_comercial=fields.Text(string="Nombre Comercial:", readonly=True)
	fecha_inscripcion=fields.Text(string="Fecha de Inscripción:", readonly=True)
	fecha_inicio_actividades=fields.Text(string="Fecha de inicio de Actividades:", readonly=True)
	estado_contribuyente=fields.Text(string="Estado del Contribuyente:", readonly=True)
	condicion_contribuyente=fields.Text(string="Condicion del Contribuyente:", readonly=True)
	domicilio_fiscal=fields.Text(string="Domicilio Fiscal:", readonly=True)
	sistema_emision_comprobante=fields.Text(string="Sistema Emisión de Comprobante:", readonly=True)
	actividad_comercio_exterior=fields.Text(string="Actividad Comercio Exterior:", readonly=True)
	sistema_contabilidad=fields.Text(string="Sistema Contabilidad:", readonly=True)
	actividad_economica=fields.Text(string="Actividad(es) Económica(s):", readonly=True)
	comprobante_pago=fields.Text(string="Comprobantes de Pago c/aut. de impresión:", readonly=True)
	sistema_emision_electronica=fields.Text(string="Sistema de Emisión Electrónica:", readonly=True)
	emisor_electronico=fields.Text(string="Emisor electrónico desde:", readonly=True)
	comprobantes_electronicos=fields.Text(string="Comprobantes Electrónicos:", readonly=True)
	afiliado_ple=fields.Text(string="Afiliado al PLE desde:", readonly=True)
	padrones=fields.Text(string="Padrones", readonly=True)
	
	type_partner = fields.Selection([
		('employee', 'Empleado'),
		('supplier', 'Proveedor'),
		('customer', 'Cliente')
	], string='Tipo Partner')
 
	def query_ruc(self):
		for i in self:
			if not i.env['res.partner'].check_ruc(i.name): 
				raise ValidationError(_(f"La entrada no es un número de RUC valido."))
			content_ruc=i.env['res.partner'].get_data(i.name)
			if len(content_ruc)!=18:
				raise ValidationError(_(f"El número de RUC no existe."))
			i.numero_ruc=content_ruc[0]
			i.tipo_contribuyente=content_ruc[1]
			i.nombre_comercial=content_ruc[2]
			i.fecha_inscripcion=content_ruc[3]
			i.fecha_inicio_actividades=content_ruc[4]
			i.estado_contribuyente=content_ruc[5]
			i.condicion_contribuyente=content_ruc[6]
			i.domicilio_fiscal=content_ruc[7]
			i.sistema_emision_comprobante=content_ruc[8]
			i.actividad_comercio_exterior=content_ruc[9]
			i.sistema_contabilidad=content_ruc[10]
			i.actividad_economica=content_ruc[11]
			i.comprobante_pago=content_ruc[12]
			i.sistema_emision_electronica=content_ruc[13]
			i.emisor_electronico=content_ruc[14]
			i.comprobantes_electronicos=content_ruc[15]
			i.afiliado_ple=content_ruc[16]
			i.padrones=content_ruc[17]

		
			# error al generar el numero aleatorio

	def get_create_partner(self):
		for i in self:
			if not self.env['res.partner'].check_ruc(self.name): 
				raise ValidationError(_(f"La entrada no es un número de RUC valido."))
			content_ruc=self.env['res.partner'].get_data(self.name)
			if len(content_ruc)!=18:
				raise ValidationError(_(f"El número de RUC no existe."))
			
			act_eco = content_ruc[11].split("\n")					
            
			context = {
				'default_name': i.numero_ruc.split("-")[1].strip(),
				'default_display_name':i.numero_ruc.split("-")[1].strip(),
				'default_vat':  i.numero_ruc.split("-")[0].strip(),
				'default_ruc_state': str(i.estado_contribuyente),
				'default_ruc_condition': str(i.condicion_contribuyente),
				'default_n2_nom_comer': str(i.nombre_comercial),
				'default_n2_sis_contab': str(i.sistema_contabilidad),
				'default_n2_see': str(i.sistema_emision_electronica),
				'default_n2_actv_econ': str(len(act_eco)),
				'default_n2_actv_econ_1': act_eco[0],
				'default_n2_actv_econ_2': act_eco[1] if len(act_eco)>1 else '',
				'default_n2_actv_econ_3': act_eco[2] if len(act_eco)>2 else '',
				'default_n2_init_actv': str(i.emisor_electronico),
				'default_n2_afi_ple': str(i.afiliado_ple),
				'default_is_partner_retencion': u"Incorporado al Régimen de Agentes de Retención" in content_ruc[17],
				'default_n2_padrones': str(i.padrones),
				'default_n2_tipo_contr': str(i.tipo_contribuyente),
				'default_l10n_latam_identification_type_id': self.env['l10n_latam.identification.type'].search([('name','=','RUC')],limit=1).id}
			return {
				'view_mode': 'form',
				'res_model': 'res.partner',
				'type': 'ir.actions.act_window',
				'context' : context,
				'target': 'new'
			}
	
	def get_create_partner_masiva(self):
		for i in self:
			if not self.env['res.partner'].search([('vat', '=', str(i.name)),('parent_id','=',False)],limit=1):				
				if not i.env['res.partner'].check_ruc(i.name): 
					raise ValidationError(_(f"La entrada no es un número de RUC valido."))
				content_ruc = i.env['res.partner'].get_data(i.name)
				if len(content_ruc) != 18:
					raise ValidationError((u'El número de RUC %s no existe o falta consultar el ruc'%(i.name)))
				act_eco = content_ruc[11].split("\n")
				vals = {
					'name': i.numero_ruc.split("-")[1].strip(),
					'display_name': i.numero_ruc.split("-")[1].strip(),
					'vat': i.numero_ruc.split("-")[0].strip(),
					'ruc_state': str(i.estado_contribuyente),
					'ruc_condition': str(i.condicion_contribuyente),
					'n2_nom_comer': str(i.nombre_comercial),
					'n2_sis_contab': str(i.sistema_contabilidad),
					'n2_see': str(i.sistema_emision_electronica),
					'n2_actv_econ': str(len(act_eco)),
					'n2_actv_econ_1': act_eco[0],
					'n2_actv_econ_2': act_eco[1] if len(act_eco) > 1 else '',
					'n2_actv_econ_3': act_eco[2] if len(act_eco) > 2 else '',
					'n2_init_actv': str(i.emisor_electronico),
					'n2_afi_ple': str(i.afiliado_ple),
					'is_partner_retencion': u"Incorporado al Régimen de Agentes de Retención" in content_ruc[17],
					'n2_padrones': str(i.padrones),
					'n2_tipo_contr': str(i.tipo_contribuyente),
					'l10n_latam_identification_type_id': i.env['l10n_latam.identification.type'].search([('name', '=', 'RUC')], limit=1).id,
					'is_employee': True if i.type_partner == 'employee' else False,
					'is_customer': True if i.type_partner == 'customer' else False,
					'is_supplier': True if i.type_partner == 'supplier' else False,
    			}
				i.env['res.partner'].create(vals)
		return self.env['popup.it'].get_message('SE CREARON LOS PARTNERS CORRECTAMENTE')

    