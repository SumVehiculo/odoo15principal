from odoo   import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime

class ProjectProject(models.Model):
    _inherit="project.project"
    

    project_name = fields.Char('Nombre del Proyecto')
    
    @api.model
    def create(self, vals):
        actual_month = str(datetime.today().month)
        date = str(datetime.today().year) + '-'
        if len(actual_month) == 1:
            # En caso el mes solo tenga un digito 
            date += '0' + actual_month
        elif len(actual_month) == 2:
            # En caso el mes tenga dos digitos
            date += actual_month
        # date = year+month
        id_seq = self.env['ir.sequence'].sudo().search([
            ('name','=','Correlativo OT SUMVEHICULOS'+date),
            ('company_id','=',self.env.company.id)
        ], limit=1)
        if not id_seq:
            id_seq = self.env['ir.sequence'].sudo().create({
                'name': 'Correlativo OT SUMVEHICULOS'+date,
                'company_id': self.env.company.id,
                'implementation': 'no_gap',
                'active': True,
                'prefix': 'OT',
                'padding': 5,
                'number_increment': 1,
                'number_next_actual': 1
            })
        vals['name'] = id_seq._next()
        return super().create(vals)