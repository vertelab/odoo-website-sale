# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution, third party addon
#    Copyright (C) 2017- Vertel AB (<http://vertel.se>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp import models, fields, api, _

import openerp
from openerp import http
from openerp.http import request

import logging
_logger = logging.getLogger(__name__)

class sale_order_minvalue(models.Model):
    _name="sale.order.minvalue"
    
    name = fields.Char()
    destination_ids = fields.Many2many(comodel_name='res.country',string="Destinations")
    pricelist_ids = fields.Many2many(comodel_name="product.pricelist",string="Price Lists")
    product_id = fields.Many2one(comodel_name="product.product",string="Order Fee",help="Product for Order Fee")
    order_fee = fields.Float(string="Order Fee",related="product_id.list_price")
    min_value = fields.Float(string="Minimum Order Value")
    info_text = fields.Text(translate=True)


class sale_order(models.Model):
    _inherit = 'sale.order'
    
    @api.one
    def _min_value_order(self):
        self.min_order_value = self.check_minimum_order_value()
    min_order_value = fields.Boolean(string='Minimum order value',compute='_min_value_order',help="Does not meet the minimum order value!")

    @api.multi
    def get_minimum_order_value(self):
        self.ensure_one()
        return self.env['sale.order.minvalue'].search([('destination_ids','in',self.partner_shipping_id.country_id.id),('pricelist_ids','in',self.pricelist_id.id)],limit=1)

   
    @api.multi
    def check_minimum_order_value(self):
        self.ensure_one()
        minvalue = self.get_minimum_order_value(self).mapped('min_value')
        if minvalue:
            return self.amount_untaxed >= minvalue
        return True
    
    @api.multi
    def action_button_confirm(self):
        self.ensureone()
        self.minimum_order_value_set()
        return super(sale_order,self).action_button_confirm()

     
    @api.multi
    def minimum_order_value_set(self):
        line_ids = []
        for order in self:
            if order.check_minimum_order_value():
                continue
            if order.state not in ('draft', 'sent'):
                raise Warning(_('Order not in Draft State!'), _('The order state have to be draft to add minimum order value lines.'))
            minvalue = order.get_minimum_order_value()


            taxes = minvalue.product_id.taxes_id.filtered(lambda t: t.company_id.id == order.company_id.id)
            taxes_ids = self.env['account.fiscal.position'].map_tax(order.fiscal_position or False, taxes)
            price_unit = minvalue.product_id.list_price
            if order.company_id.currency_id.id != order.pricelist_id.currency_id.id:
                price_unit = self.env['res.currency'].compute(order.company_id.currency_id.id, order.pricelist_id.currency_id.id, price_unit,date=order.date_order)
            values = {
                'order_id': order.id,
                'name': minvalue.product_id.name,
                'product_uom_qty': 1,
                'product_uom': minvalue.product_id.uom_id.id,
                'product_id': minvalue.product_id.id,
                'price_unit': price_unit,
                'tax_id': [(6, 0, taxes_ids)],
            }
            res = self.env['sale.order.line'].product_id_change(order.pricelist_id.id, values['product_id'],
                                             qty=values['product_uom_qty'], uom=False, qty_uos=0, uos=False, name='', partner_id=order.partner_id.id,
                                             lang=False, update_tax=True, date_order=False, packaging=False, fiscal_position=order.fiscal_position, flag=False,)
            if res['value'].get('purchase_price'):
                values['purchase_price'] = res['value'].get('purchase_price')
            if order.order_line:
                values['sequence'] = order.order_line[-1].sequence + 1
            line_id = self.env['sale.order.line'].create(values)
            line_ids.append(line_id)
        return line_ids

        
class website(models.Model):
    _inherit = 'website'

    @api.model
    def check_minimum_order_value(self):
        sale_order = request.env['sale.order'].sudo().browse(request.session.get('sale_order_id'))
        if not sale_order:
            _logger.warning('Check minimum order value, missing sale-order %s' % request.session.get('sale_order_id'))
            return ''
        minvalue = request.env['sale.order.minvalue'].search([('destination_ids','in',sale_order.partner_shipping_id.country_id.id)],limit=1)
        if minvalue:
            if sale_order.amount_untaxed < minvalue.min_value:
                return minvalue.info_text
        return ''


#~ class website_sale(website_sale.http.Controller):

    #~ @http.route(['/shop/order/note'], type='json', auth="public", website=True)
    #~ def order_note(self, note, **post):
        #~ order = request.website.sudo().sale_get_order()
        #~ if order:
            #~ order.sudo().note = note

    #~ @http.route(['/shop/confirm_order'], type='http', auth="public", website=True)
    #~ def confirm_order(self, **post):
        #~ cr, uid, context, registry = request.cr, request.uid, request.context, request.registry

        #~ order = request.website.sale_get_order(context=context)
        #~ if not order:
            #~ return request.redirect("/shop")

        #~ redirection = self.checkout_redirection(order)
        #~ if redirection:
            #~ return redirection

        #~ values = self.checkout_values(post)

        #~ values["error"] = self.checkout_form_validate(values["checkout"])
        #~ if values["error"]:
            #~ return request.website.render("website_sale.checkout", values)

        #~ self.checkout_form_save(values["checkout"])

        #~ request.session['sale_last_order_id'] = order.id

        #~ request.website.sale_get_order(update_pricelist=True, context=context)

        #~ return request.redirect("/shop/payment")

