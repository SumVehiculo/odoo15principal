from odoo import models, fields

class ProjectTags(models.Model):
    _inherit="project.tags"
    
    company_id = fields.Many2one(
        'res.company', 
        string='Compañia',
        default= lambda self: self.env.company.id
    )