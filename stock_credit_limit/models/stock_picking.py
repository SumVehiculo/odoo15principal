# -*- coding: utf-8 -*-

from ast import Pass
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo import tools


class stock_picking(models.Model):
    _inherit = 'stock.picking'
    state_credit_limit = fields.Char("Estado De Crédito")
    date_credit_verify = fields.Date("Fecha Verificación Crédito")       
                        
    def button_validate(self):        
        for order in self:
            if order.partner_id.parent_id.id:
                partner_padre = order.partner_id.parent_id
            else:
                partner_padre = order.partner_id
            if partner_padre.credit_limit != 0:            
                import datetime
                from datetime import timedelta
                order.state_credit_limit = "Ok"
                order.date_credit_verify = (datetime.datetime.now() - timedelta(hours=5)).date()
                if order.location_id.usage == 'internal' and order.location_dest_id.usage == 'customer':
                    facturas = self.env['account.move'].sudo().search([('partner_id','=',partner_padre.id),('company_id','=',order.company_id.id), ('state','=','posted'),('move_type','in',['out_invoice'])])
                    vencidos = []
                    credito_mas_venta = 0
                    credito = 0
                    if len(facturas)>0:
                        for factura in facturas:
                            if factura.vencido == "Vencida":
                                vencidos.append(factura)
                        if len(vencidos)>0:
                            mensaje = ""
                            for m in vencidos:
                                mensaje += str(m.ref)+ " │ Total: "+str(m.amount_total) + " │ Fecha de Vencimiento: "+str(m.invoice_date_due) + "\n"
                            raise UserError("No Se Puede Validar El Albaran, El Cliente Tiene Facturas Vencidas: " + "\n" + mensaje)
                        credito = 0                    
                        credito_mas_venta = 0
                        for f in facturas:
                            if f.amount_residual != 0:                            
                                if f.currency_id == partner_padre.moneda:
                                    credito += f.amount_residual
                                    credito_mas_venta += f.amount_residual
                                else:
                                    tasa_cambio = self.env['res.currency.rate'].search([('currency_id.name','=','USD'),('name','=', f.invoice_date),('company_id','=',f.company_id.id)], limit=1)
                                    if tasa_cambio:
                                        if partner_padre.moneda.name == 'USD':
                                            tasa_cambio_valor_venta = tasa_cambio.sale_type
                                            credito += f.amount_residual / tasa_cambio_valor_venta
                                            credito_mas_venta += f.amount_residual / tasa_cambio_valor_venta    
                                        elif partner_padre.moneda.name == 'PEN':
                                            tasa_cambio_valor_venta = tasa_cambio.sale_type
                                            credito += f.amount_residual * tasa_cambio_valor_venta
                                            credito_mas_venta += f.amount_residual * tasa_cambio_valor_venta
                                        else:
                                            raise UserError("no hay tasa de cambio Las Monedas Autorizadas para Limites de credito de el Contacto Son Soles y Dolares")
                                    else:
                                        raise UserError("no hay tasa de cambio en Dolar a la fecha para la factura " + str(f.name))
                                    

                    precio_venta = 0
                    venta_actual = []                    
                    for lineas in order.move_ids_without_package:
                        if lineas.sale_line_id:                            
                            if lineas.sale_line_id.order_id in venta_actual:
                                pass
                            else:
                                venta_actual.append(lineas.sale_line_id.order_id)
                    if len(venta_actual)>0:
                        for vnta in venta_actual:                            
                            for lineas_venta in vnta.order_line:
                                cantidad_facturada = 0
                                if lineas_venta.invoice_lines:                                        
                                    for lineas_factura in lineas_venta.invoice_lines:
                                        if lineas_factura.move_id.state == 'posted':
                                            cantidad_facturada += lineas_factura.quantity
                                            pass
                                        else:
                                            pass
                                    precio_unitario_linea_venta = lineas_venta.price_total / lineas_venta.product_uom_qty
                                    precio_no_facturadas = precio_unitario_linea_venta * (lineas_venta.product_uom_qty - cantidad_facturada)
                                    precio_venta += precio_no_facturadas
                                else:
                                    precio_unitario_linea_venta = lineas_venta.price_total / lineas_venta.product_uom_qty
                                    precio_no_facturadas = precio_unitario_linea_venta * (lineas_venta.product_uom_qty - cantidad_facturada)
                                    precio_venta += precio_no_facturadas                                        
                    if precio_venta >0:                        
                        if lineas_venta.order_id.pricelist_id.currency_id.id == partner_padre.moneda.id:
                            credito_mas_venta += precio_venta
                        else:
                            import datetime
                            from datetime import timedelta
                            tasa_cambio = self.env['res.currency.rate'].search([('currency_id.name','=','USD'),('name','=', (lineas_venta.order_id.date_order - timedelta(hours=5)).date()),('company_id','=',lineas_venta.order_id.company_id.id)], limit=1)
                            if tasa_cambio:
                                if partner_padre.moneda.name == 'USD':
                                    tasa_cambio_valor_venta = tasa_cambio.sale_type
                                    credito_mas_venta += precio_venta / tasa_cambio_valor_venta
                                    
                                elif partner_padre.moneda.name == 'PEN':
                                    tasa_cambio_valor_venta = tasa_cambio.sale_type
                                    credito_mas_venta += precio_venta * tasa_cambio_valor_venta
                                else:
                                    raise UserError("no hay tasa de cambio Para El Cliente Las Monedas Autorizadas Son Soles y Dolares")
                            else:
                                raise UserError("no hay tasa de cambio a la fecha para la Venta" + str(lineas_venta.order_id.name)+ " Del Actual Albaran.")
                                                                                    
                    if partner_padre.moneda != False and (partner_padre.credit_limit - credito_mas_venta)<0:
                        raise UserError("El Cliente Tiene "+str(partner_padre.moneda.symbol)+" "+ str(credito) + " Por Pagar En Facturas. " + " El Credito Del Cliente es: " +str(partner_padre.moneda.symbol)+" "  + str(partner_padre.credit_limit) + ". Tu Saldo Restante Es: "+str(partner_padre.moneda.symbol)+" " +  str(partner_padre.credit_limit - credito)+" Tu Credito Faltante Con las Lineas De Venta Aun No Facturadas es: "+  str(partner_padre.credit_limit - credito_mas_venta))
                    import datetime
                    from datetime import timedelta
                    order.state_credit_limit = 'Credito OK'
                    order.date_credit_verify = (datetime.datetime.now() - timedelta(hours=5)).date()
        t = super(stock_picking,self).button_validate()
        return t



    def view_credit(self):
        for i in self:
            if i.partner_id.id:
                if i.partner_id.parent_id.id:
                    partner_padre = i.partner_id.parent_id
                else:
                    partner_padre = i.partner_id
                if partner_padre.credit_limit != 0:
                    facturas = self.env['account.move'].sudo().search([('partner_id','=',partner_padre.id),('company_id','=',i.company_id.id), ('state','=','posted'),('move_type','in',['out_invoice'])])
                    facturas_view = []
                    info = ""
                    enviar = False
                    if len(facturas)>0:
                        mensaje = ""
                        vencido_msg = ""
                        monto_total_moneda_cliente = 0.00
                        for f in facturas:                            
                            if f.vencido == "Vencida" or f.amount_residual != 0:
                                enviar = True
                                if f.currency_id == partner_padre.moneda:
                                    if f.vencido == "Vencida":
                                        vencido_msg = " │ "+ "Factura Vencida"
                                    mensaje += str(f.name) + " │ "+ "Facturada Con La Misma Moneda Que El Crédito Del Cliente.  Total:" + " │ " + str(partner_padre.moneda.symbol)+ str(f.amount_residual)+ vencido_msg +  "\n"
                                    monto_total_moneda_cliente += f.amount_residual
                                else:                            
                                    tasa_cambio = self.env['res.currency.rate'].search([('currency_id.name','=','USD'),('name','=', f.invoice_date),('company_id','=',f.company_id.id)], limit=1)
                                    if tasa_cambio:
                                        if f.vencido == "Vencida":
                                            vencido_msg = " │ "+ "Factura Vencida"                                        
                                        if partner_padre.moneda.name == 'USD':
                                            mensaje += str(f.name) + " │ "+ "Facturada Con La Moneda "+ str(f.currency_id.symbol)+ " │ "+ "Total: "+str(f.amount_residual)+ " │ "+ "Tasa De Cambio: "+str(tasa_cambio.sale_type) +" │ "+"Total En Tasa de Cambio: "+str(f.amount_residual / tasa_cambio.sale_type)+vencido_msg  +"\n"
                                            tasa_cambio_valor_venta = tasa_cambio.sale_type
                                            monto_total_moneda_cliente += f.amount_residual / tasa_cambio_valor_venta
                                        if partner_padre.moneda.name == 'PEN':
                                            mensaje += str(f.name) + " │ "+ "Facturada Con La Moneda "+ str(f.currency_id.symbol)+ " │ "+ "Total: "+str(f.amount_residual)+ " │ "+ "Tasa De Cambio: "+str(tasa_cambio.sale_type) +" │ "+"Total En Tasa de Cambio: "+str(f.amount_residual * tasa_cambio.sale_type)+vencido_msg  +"\n"
                                            tasa_cambio_valor_venta = tasa_cambio.sale_type
                                            monto_total_moneda_cliente += f.amount_residual * tasa_cambio_valor_venta
                                        if partner_padre.moneda.name != 'PEN' and partner_padre.moneda.name != 'USD':
                                            raise UserError("no hay tasa de cambio Las Monedas Autorizadas Para Limites de Creditos del Contacto Son Soles y Dolares")
                                    else:
                                        mensaje += "no hay tasa de cambio a la fecha para la factura " + str(f.name)+"Si Esto Se Produjo Por Eliminacion De Una Tasa de Cambio, Por Favor Crearla Nuevamente"+"\n"
                        if enviar==True:
                            info = mensaje + "\n" + "Total Facturas: " + str(partner_padre.moneda.symbol)+ str(monto_total_moneda_cliente) + " Credito Del Cliente: " + str(partner_padre.moneda.symbol)+ str(partner_padre.credit_limit) + " Crédito Restante Del Cliente con el Total Facturas: " + str(partner_padre.moneda.symbol) + str(partner_padre.credit_limit - monto_total_moneda_cliente)

                        for factura in facturas:
                            factura.refresh()
                            if factura.vencido == "Vencida":
                                if factura in facturas_view:
                                    pass
                                else:
                                    facturas_view.append(factura)
                            if factura.amount_residual != 0:
                                if factura in facturas_view:
                                    pass
                                else:
                                    facturas_view.append(factura)
                    if len(facturas_view)>0:                    
                        ctx = {
                        'default_name': partner_padre.id,
                        'default_moneda': partner_padre.moneda.id if partner_padre.moneda.id else False,
                        'default_state': 'draft',
                        'default_total_tasa_cambio_text' : info,
                        }
                        return {
                            'name': _('Historial'),
                            'type': 'ir.actions.act_window',
                            'view_type': 'form',
                            'view_mode': 'form',
                            'target': 'new',
                            'res_model': 'sale.history',
                            'context': ctx,
                            }                                
                    else:                    
                        ctx = {                                
                        'default_name': partner_padre.id,
                        'default_moneda': partner_padre.moneda.id if partner_padre.moneda.id else False,
                        'default_state': 'draft',
                        'default_total_tasa_cambio_text' : info,
                        }
                        return {
                            'name': _('Historial'),
                            'type': 'ir.actions.act_window',
                            'view_type': 'form',
                            'view_mode': 'form',
                            'target': 'new',
                            'res_model': 'sale.history',
                            'context': ctx,
                            }
                else:
                    ctx = {                                
                        'default_name': partner_padre.id,
                        'default_moneda': partner_padre.moneda.id if partner_padre.moneda.id else False,
                        'default_state': 'draft',                        
                        }
                    return {
                        'name': _('Historial'),
                        'type': 'ir.actions.act_window',
                        'view_type': 'form',
                        'view_mode': 'form',
                        'target': 'new',
                        'res_model': 'sale.history',
                        'context': ctx,
                        }
           
           