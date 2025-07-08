from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'
    
    uniform_delivery_report = fields.Boolean('Habilitar Reporte de Uniformes')
    uniform_delivery_content = fields.Html(
        string='Reporte de Entrega EPP',
        default= lambda self:
        f"""
        <p>
            Quien suscribe declara recibir a su entera conformidad el(los) Elemento(s) de Protección Personal (EPP) y/o uniformes que arriba se detalla, cuyo sentido no es más que su protección y cumplimiento de la normativa de seguridad vigente.<br/>
            <br/>
            Asimismo, doy cuenta que conozco la manera de utilizarlo correctamente y que he sido instruido en su uso, y me comprometo a utilizarlo en todo momento durante mi jornada de trabajo, a cuidarlos y hacer entrega de los mismos una vez terminada la relación con la Empresa, toda vez que me han sido otorgados en forma gratuita, pero siguen siendo propiedad de {self.env.company.name}.<br/>
            <br/>
            Me hago responsable de informar a mi Jefatura en caso de extravío, hurto o deterioro, aceptando lo estipulado en el Reglamento Interno de Trabajo, así como en el Reglamento Interno de Seguridad y Salud en el Trabajo, en caso de esos hechos o del NO USO o USO INDEBIDO.<br/>
            En caso de término de vínculo laboral y la empresa solicite la devolución de los equipos de protección personal entregados, soy responsable de la devolución o de lo contrario autorizo se me descuente de la liquidación de beneficios.
        </p>
        """
    )
    