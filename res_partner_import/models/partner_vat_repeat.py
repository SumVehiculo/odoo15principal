# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


#class res_partner(models.Model):
    #_inherit = "res.partner"

    #@api.constrains('l10n_latam_identification_type_id','vat','parent_id')
    #def check_vat(self):
        #for i in self:
            #if i.vat:
                #if i.l10n_latam_identification_type_id:
                    #if i.parent_id:
                        #pass
                    #else:
                        #no_repetido_vat = self.env['res.partner'].search([('vat','=',i.vat),('l10n_latam_identification_type_id','=',i.l10n_latam_identification_type_id.id),('parent_id','=',False)])
                        #for repetido in no_repetido_vat:
                            #if repetido.id != i.id:
                                #raise UserError("Contactos Duplicados Con Tipo Identificacion: " + str(i.l10n_latam_identification_type_id.name) + " Con Número De Identificacion: "+str(i.vat))